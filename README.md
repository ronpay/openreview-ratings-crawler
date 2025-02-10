# Openreview Ratings Crawler

A lightweight Python tool for extracting average review ratings from OpenReview conferences using venue ID and year parameters.

# Usage

```shell
python main.py --venue ACM.org/TheWebConf --year 2025
```

# Notes

+ Currently pre-configured for TheWebConf 2025 structure.
+ For other conferences, modify data extraction logic in code.

# Roadmap

+  Add configurable score key mappings and generalize parsing logic for multiple conference formats.

# Acknowleges
This project incorporates code adapted from [openreview-visualization](https://github.com/ranpox/openreview-visualization).