# DAZN Competitive Intelligence Framework

A powerful, entirely local data scraping and Natural Language Processing (NLP) dashboard designed to analyze the competitive sports streaming landscape. 

It tracks real-time customer sentiment, developer response volume, and root-cause UX friction across DAZN, ESPN, Sky Sports, FuboTV, and others.

---

## Architecture
The system consists of three distinct phases:

1. **The Scraping Engine (`src/scrape_reviews.py` & `src/scrape_metrics.py`)**: 
   A hybrid architecture utilizing raw HTTPX requests (`google-play-scraper`) and Playwright stealth browsers. It extracts thousands of live reviews and developer responses from Google Play, Apple App Store, and Trustpilot, completely bypassing expensive API paywalls. Data is mapped to local CSV dataframes.

2. **The NLP Engine (`src/issue_categorizer.py` & `src/nlp_analyzer.py`)**: 
   Uses `scikit-learn` and `nltk` to perform keyword frequency analysis and text categorization on 1-Star and 2-Star reviews, grouping complaints into "App Stability", "Content & UX", and "Billing Friction".

3. **The Executive Dashboard (`app.py`)**: 
   A lightweight but highly advanced **Streamlit** presentation layer that bridges directly to the Pandas CSVs to render real-time interactive Plotly charts, Treemaps, and Sentiment Heatmaps.

## Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/logicalninja/dazncomp.git
cd dazncomp
```

**2. Initialize the Python Virtual Environment**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```
*(Optionally, Playwright may require downloading its browser binaries post-install: `playwright install chromium`)*

## Running the Executive Dashboard
You do not need to scrape fresh data to run the UI; a static dataset (`data/metrics_database.csv` & `data/reviews_database.csv`) is preserved in the repository so the interface works out of the box.

From the root directory with your virtual environment active, simply run:
```bash
PYTHONPATH=src streamlit run app.py
```
*The dashboard will automatically launch in your default web browser at `http://localhost:8501/`.*

---
### Key Insights Captured:
* **Ecosystem Volume:** DAZN leads the European core market with 638,000 public reviews, dwarfing direct rivals like Sky Sports (90k) and BT Sport (25k).
* **Support Engine:** DAZN effectively resolves public platform complaints with a massive 81% response rate and lightning-fast sub-4-hour response speeds.
* **Root Cause Friction:** Despite excellent app stability and developer support, DAZN is disproportionately impacted by "Billing Friction" compared to American rivals like ESPN (whose users primarily complain about digital TV provider authentication).

