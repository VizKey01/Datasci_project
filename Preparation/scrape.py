import requests
import time
import json
import csv
import pandas as pd
from datetime import datetime

def fetch_crossref_articles(query, limit_per_page=20, output_file=None):
    base_url = "https://api.crossref.org/works"
    fields = "title,abstract,published,author"
    
    # Query parameters
    params = {
        "query": query,
        "select": fields,
        "rows": limit_per_page,
        "filter": "has-abstract:true,has-affiliation:true",
        "cursor": "*"
    }
    
    results = []
    cursor = "*"
    
    while cursor:
        print(f"Fetching results with cursor {cursor}...")
        try:
            response = requests.get(base_url, params=params, timeout=30)  # Set timeout
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        except requests.exceptions.Timeout:
            print("Request timed out. Retrying...")
            time.sleep(10)  # Retry after a short delay
            continue
        except requests.exceptions.ConnectionError:
            print("Connection error occurred. Check your internet or the API's status.")
            break
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            break
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred: {req_err}")
            break
        # Handle rate limiting
        if response.status_code == 429:
            print("Rate limit reached. Waiting for 10 seconds before retrying...")
            time.sleep(10)
            continue
        
        # Handle other errors
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code}, {response.text}")
            break
        
        data = response.json()

        # Check for no results
        items = data.get('message', {}).get('items', [])
        if not items:
            print("No more results available.")
            break

        # Append results
        results.extend(items)

        print(f"Total results fetched: {len(results)}")
        
        # Get next cursor
        cursor = data.get('message', {}).get('next-cursor', None)
        params['cursor'] = cursor

        time.sleep(1.5)  # To avoid hitting rate limits
    
    print(f"Fetched {len(results)} results.")
    
    if results:
        processed_results = []
        for paper in results:    
            if not paper.get('author') or not paper.get('author')[0].get('affiliation') or not paper.get('published')or not paper.get('abstract'):
                continue
            if paper.get('published').get('date-parts')[0][0] == None:
                continue
            if paper.get('abstract') == None:
                continue
            if paper.get('author')[0].get('affiliation')[0].get('name') == None:
                continue
            processed_paper = {
                'title': paper.get('title')[0].strip(),
                'affiliation': paper.get('author')[0].get('affiliation')[0].get('name').strip(),
                'year': paper.get('published').get('date-parts')[0][0],
                'abstract': paper.get('abstract').strip(),
            }
            processed_results.append(processed_paper)

        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"crossref_{query.replace(' ', '_')}_{timestamp}.csv"

        df = pd.DataFrame(processed_results)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Results saved to {output_file}")

    return results

# Example usage
results = fetch_crossref_articles(
    query="carbon emissions",
    limit_per_page=1000,
    output_file="crossref_papers.csv"
)