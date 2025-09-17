# scraper/fetch_search_results.py
# Usage: set env variables GOOGLE_API_KEY and GOOGLE_CX, then run:
#   python fetch_search_results.py --query "free cricket browser games" --max 10

import os
import json
import time
import argparse
from datetime import datetime
from urllib.parse import urlencode
import requests

API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX")
BASE_URL = "https://www.googleapis.com/customsearch/v1"

if not API_KEY or not CX:
    raise SystemExit("Set environment variables GOOGLE_API_KEY and GOOGLE_CX before running.")

def fetch(query, start=1, num=10):
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
        "start": start,
        "num": num,
    }
    url = BASE_URL + "?" + urlencode(params)
    headers = {"User-Agent": "SEO-Playground-Scraper/1.0 (+https://ishaan-bhardwaj-profile.github.io/)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()

def normalize_item(item):
    # Only keep safe metadata fields to store
    return {
        "title": item.get("title"),
        "snippet": item.get("snippet"),
        "link": item.get("link"),
        "displayLink": item.get("displayLink"),
        "mime": item.get("mime"),
    }

def run_searches(queries, max_results_per_query=10, output_dir="scraper_output"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H%M%SZ")
    out = {"timestamp": timestamp, "queries": []}

    for q in queries:
        print(f"Searching: {q}")
        items = []
        fetched = 0
        start = 1
        while fetched < max_results_per_query:
            to_fetch = min(10, max_results_per_query - fetched)
            data = fetch(q, start=start, num=to_fetch)
            results = data.get("items", [])
            for r in results:
                items.append(normalize_item(r))
            fetched += len(results)
            if len(results) < to_fetch:
                break
            start += len(results)
            time.sleep(1)  # polite pause
        out["queries"].append({"query": q, "results_count": len(items), "results": items})
    # write file
    filename = f"{output_dir}/results-{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Saved:", filename)
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q", action="append", help="A query to search. Repeat to add multiple.", required=True)
    parser.add_argument("--max", type=int, default=10, help="Max results per query (default=10).")
    parser.add_argument("--out", default="scraper_output", help="Output directory.")
    args = parser.parse_args()

    run_searches(args.query, max_results_per_query=args.max, output_dir=args.out)
