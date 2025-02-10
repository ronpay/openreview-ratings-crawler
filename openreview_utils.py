import requests
from tqdm import tqdm
import concurrent.futures
import pandas as pd
import statistics
from tqdm import tqdm

class OpenReviewFetcher:
    BASE_URL = "https://api2.openreview.net/notes"
    HEADERS = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "sec-ch-ua": '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
    }

    def __init__(self, venue, year, batch_limit=1000, limit=-1):
        self.venue = venue
        self.year = year
        self.batch_limit = batch_limit
        self.limit = limit

    def fetch_papers(self):
        url = f"{self.BASE_URL}?content.venueid={self.venue}%2F{self.year}%2FConference&details=replyCount%2Cinvitation%2Coriginal&domain={self.venue}%2F{self.year}%2FConference"
        initial_data = self._fetch_data(url)
        count = initial_data["count"]
        print(url)
        print(f"Total number of papers: {count}")
        print(f"Batch limit: {self.batch_limit}")
        print(f"Limit: {self.limit}")
        all_papers = []
        for offset in tqdm(range(0, count, self.batch_limit)):
            data = self._fetch_data(f"{url}&limit={self.batch_limit}&offset={offset}")
            all_papers.extend(data["notes"])
            if self.limit != -1 and len(all_papers) >= self.limit:
                break

        return all_papers, count

    def fetch_reviews(self, paper_ids):
        base_url = f"{self.BASE_URL}?details=replyCount%2Cwritable%2Csignatures%2Cinvitation%2Cpresentation&domain={self.venue}%2F{self.year}%2FConference&forum="

        with requests.Session() as session:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(self._fetch_data, f"{base_url}{paper_id}", session) for paper_id in paper_ids
                ]
                return [
                    future.result() for future in tqdm(concurrent.futures.as_completed(futures), total=len(paper_ids))
                ]

    def _fetch_data(self, url, session=None):
        if session:
            response = session.get(url, headers=self.HEADERS)
        else:
            response = requests.get(url, headers=self.HEADERS)
        return response.json()


class OpenReviewProcessor:
    @staticmethod
    def process_papers(papers):
        # df = pd.json_normalize(papers)
        papers = pd.json_normalize(
            papers.to_dict('records'),
            sep='.',
        )
        print("Available columns:", papers.columns.tolist())
        filtered_df = papers[
            [
                "id",
                "content.title.value",
                "content.abstract.value",
                "content.track.value",
                "content.keywords.value",
                "content.venue.value",
            ]
        ]
        filtered_df.columns = ["id", "title", "abstract", "track", "keywords", "venue"]
        return filtered_df

    @staticmethod
    def process_reviews(reviews):
        # turn reviews to list of dict
        reviews = reviews.to_dict('records')
        processed_data = []
        for review in tqdm(reviews):
            paper_id = None
            title = ""
            track = ""
            ratings = {
                'scope': [],
                'novelty': [],
                'technical_quality': [],
                'reviewer_confidence': [],
            }

            for note in review["notes"]:
                if "title" in note["content"]:
                    title = note["content"]["title"]["value"]
                    paper_id = note["id"]
                    try:
                        track = note["content"]["track"]["value"]
                    except KeyError:
                        track = "N/A"
                        print(f"Track not found for paper {paper_id}")
                elif "novelty" in note["content"]:
                    novelty = int(note["content"]["novelty"]["value"].split(":")[0])
                    ratings["novelty"].append(novelty)
                    scope = int(note["content"]["scope"]["value"].split(":")[0])
                    ratings["scope"].append(scope)
                    technical_quality = int(note["content"]["technical_quality"]["value"].split(":")[0])
                    ratings["technical_quality"].append(technical_quality)
                    reviewer_confidence = int(note["content"]["reviewer_confidence"]["value"].split(":")[0])
                    ratings["reviewer_confidence"].append(reviewer_confidence)

            if ratings["novelty"]:
                avg_novelty = sum(ratings["novelty"]) / len(ratings["novelty"])
                std_novelty = statistics.stdev(ratings["novelty"]) if len(ratings["novelty"]) > 1 else 0
                avg_technical = sum(ratings["technical_quality"]) / len(ratings["technical_quality"])
                std_technical = statistics.stdev(ratings["technical_quality"]) if len(ratings["technical_quality"]) > 1 else 0
                avg_scope = sum(ratings["scope"]) / len(ratings["scope"])
                std_scope = statistics.stdev(ratings["scope"]) if len(ratings["scope"]) > 1 else 0
                avg_confidence = sum(ratings["reviewer_confidence"]) / len(ratings["reviewer_confidence"])
                std_confidence = statistics.stdev(ratings["reviewer_confidence"]) if len(ratings["reviewer_confidence"]) > 1 else 0
                paper_ratings = {
                    "avg_novelty": avg_novelty,
                    "std_novelty": std_novelty,
                    "avg_technical": avg_technical,
                    "std_technical": std_technical,
                    "avg_scope": avg_scope,
                    "std_scope": std_scope,
                    "avg_confidence": avg_confidence,
                    "std_confidence": std_confidence
                }
            else:
                paper_ratings = {
                    "avg_novelty": None,
                    "std_novelty": None,
                    "avg_technical": None,
                    "std_technical": None,
                    "avg_scope": None,
                    "std_scope": None,
                    "avg_confidence": None,
                    "std_confidence": None
                }

            processed_data.append(
                {
                    "id": paper_id,
                    "title": title,
                    "track": track,
                    "avg_novelty": paper_ratings["avg_novelty"],
                    "std_novelty": paper_ratings["std_novelty"],
                    "avg_technical": paper_ratings["avg_technical"],
                    "std_technical": paper_ratings["std_technical"],
                    "avg_scope": paper_ratings["avg_scope"],
                    "std_scope": paper_ratings["std_scope"],
                    "avg_confidence": paper_ratings["avg_confidence"],
                    "std_confidence": paper_ratings["std_confidence"]
                }
            )

        return pd.DataFrame(processed_data)