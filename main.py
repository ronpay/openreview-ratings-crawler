import openreview
import json
import pandas as pd
from dotenv import load_dotenv
import os
import argparse
from tqdm import tqdm
from pathlib import Path

from openreview_utils import OpenReviewFetcher, OpenReviewProcessor

parser = argparse.ArgumentParser()
parser.add_argument("--venue", type=str, help="Venue ID", default='ACM.org/TheWebConf')
parser.add_argument("--year", type=int, help="Year", default=2025)

args = parser.parse_args()
venue = args.venue
year = args.year

data_path = Path('data')
note_path = data_path / f'{venue.split("/")[-1]}_{year}_notes.jsonl'
paper_path = data_path / f'{venue.split("/")[-1]}_{year}_papers.json'
review_path = data_path / f'{venue.split("/")[-1]}_{year}_reviews.json'
rating_path = data_path / f'{venue.split("/")[-1]}_{year}_ratings.json'

if not data_path.exists():
    data_path.mkdir()

# fetch notes by venue and year
if not note_path.exists():
    fetcher = OpenReviewFetcher(
        venue=venue,
        year=year,
    )

    notes, cnt = fetcher.fetch_papers()
    print(f'Fetched {cnt} notes from {venue}/{year}')

    # save notes to {venue}_{year}.jsonl
    with open(note_path, 'w') as f:
        for note in notes:
            f.write(json.dumps(note) + '\n')
    # turn notes(list of dict) into pandas dataframe
    # notes_df = pd.Datanotes_df = pd.read_json(note_path, lines=True)Frame(notes)
    notes_df = pd.read_json(note_path, lines=True)
else:
    notes_df = pd.read_json(note_path, lines=True)

if not paper_path.exists():
    papers_df = OpenReviewProcessor.process_papers(notes_df)
    papers_df.to_json(paper_path, orient='records', lines=True)
    print("Available columns:", notes_df.columns.tolist())
else:
    papers_df = pd.read_json(paper_path, lines=True)

if not review_path.exists():
    fetcher = OpenReviewFetcher(
        venue=venue,
        year=year,
    )
    paper_ids = papers_df["id"].tolist()
    reviews_df = fetcher.fetch_reviews(paper_ids)
    print(f'Fetched {len(reviews_df)} reviews from {venue}/{year}')

    with open(review_path, 'w') as f:
        for review in reviews_df:
            f.write(json.dumps(review) + '\n')
    reviews_df = pd.read_json(review_path, lines=True)
else:
    reviews_df = pd.read_json(review_path, lines=True)
    
if not rating_path.exists():
    ratings_df = OpenReviewProcessor.process_reviews(reviews_df)
    ratings_df.to_json(rating_path, orient='records', lines=True)
    print(f'Saved ratings to {rating_path}')
else:
    ratings_df = pd.read_json(rating_path, lines=True)


ratings_df.groupby('track')[['avg_novelty', 'avg_technical', 'avg_confidence']].mean()

# get avg novelty and technical quality for each track
average_rating = ratings_df.groupby('track')[['avg_novelty', 'avg_technical', 'avg_confidence']].mean()
print(average_rating)