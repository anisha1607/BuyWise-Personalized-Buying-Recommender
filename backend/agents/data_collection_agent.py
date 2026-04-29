import os
import json
import glob
import pandas as pd
import requests
import re
import httpx
from typing import List, Dict, Optional
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _norm(record: dict) -> dict:
    return {
        "source": str(record.get("source", "unknown")),
        "product": str(record.get("product", "")),
        "rating": float(record.get("rating", 3.0)),
        "text": str(record.get("text", "")),
        "date": str(record.get("date", datetime.now().strftime("%Y-%m-%d"))),
    }


def _flexible_rating(row: dict) -> float:
    for key in ("rating", "stars", "score", "overall", "overall_rating"):
        if key in row and row[key] is not None:
            try:
                return float(row[key])
            except (ValueError, TypeError):
                continue
    return 3.0


def _flexible_text(row: dict) -> str:
    for key in ("text", "review_text", "reviewText", "body", "content", "comment"):
        if key in row and row[key]:
            return str(row[key])
    return ""


def _flexible_date(row: dict) -> str:
    for key in ("date", "reviewTime", "review_date", "timestamp", "unixReviewTime"):
        if key in row and row[key]:
            val = row[key]
            # Unix timestamp (UCSD Amazon format)
            if str(val).isdigit() and int(str(val)) > 1_000_000_000:
                try:
                    return datetime.fromtimestamp(int(val)).strftime("%Y-%m-%d")
                except Exception:
                    pass
            return str(val)[:10]
    return datetime.now().strftime("%Y-%m-%d")


def _source_from_path(path: str) -> str:
    name = os.path.basename(path).lower()
    if "amazon" in name:
        return "Amazon"
    if "bestbuy" in name or "best_buy" in name:
        return "BestBuy"
    if "yelp" in name:
        return "Yelp"
    if "trustpilot" in name:
        return "Trustpilot"
    return "Kaggle"


def load_file_reviews(product_name: str) -> List[Dict]:
    reviews: List[Dict] = []
    q = product_name.lower()
    data_dir = os.path.normpath(DATA_DIR)

    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    for path in csv_files:
        try:
            df = pd.read_csv(path, low_memory=False)
            src = _source_from_path(path)
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                # Filter by product if a product column exists
                product_val = str(row_dict.get("product", row_dict.get("asin", ""))).lower()
                if product_val and q not in product_val:
                    continue
                text = _flexible_text(row_dict)
                if not text:
                    continue
                reviews.append({
                    "source": row_dict.get("source", src),
                    "product": row_dict.get("product", row_dict.get("asin", product_name)),
                    "rating": _flexible_rating(row_dict),
                    "text": text,
                    "date": _flexible_date(row_dict),
                })
        except Exception:
            continue

    json_files = glob.glob(os.path.join(data_dir, "*.json"))
    for path in json_files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                continue
            src = _source_from_path(path)
            for rec in data:
                if not isinstance(rec, dict):
                    continue
                product_val = str(rec.get("product", rec.get("asin", ""))).lower()
                if product_val and q not in product_val:
                    continue
                text = _flexible_text(rec)
                if not text:
                    continue
                reviews.append({
                    "source": rec.get("source", src),
                    "product": rec.get("product", rec.get("asin", product_name)),
                    "rating": _flexible_rating(rec),
                    "text": text,
                    "date": _flexible_date(rec),
                })
        except Exception:
            continue

    jsonl_files = glob.glob(os.path.join(data_dir, "*.jsonl"))
    for path in jsonl_files:
        try:
            src = _source_from_path(path)
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    product_val = str(rec.get("product", rec.get("asin", ""))).lower()
                    if product_val and q not in product_val:
                        continue
                    text = _flexible_text(rec)
                    if not text:
                        continue
                    reviews.append({
                        "source": rec.get("source", src),
                        "product": rec.get("product", rec.get("asin", product_name)),
                        "rating": _flexible_rating(rec),
                        "text": text,
                        "date": _flexible_date(rec),
                    })
        except Exception:
            continue

    return reviews


def load_pasted_reviews(text: str, product_name: str) -> List[Dict]:
    """
    Splits pasted text into manageable snippets and treats them as personal reviews.
    """
    # Simple split by paragraph or double newline
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    results = []
    for p in paragraphs:
        results.append({
            "source": "Personal",
            "text": p,
            "rating": 3, # Default neutral rating, sentiment agent will refine this
            "product": product_name,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    return results


def load_trustpilot_reviews(product: str) -> pd.DataFrame:
    # Trustpilot is currently blocked by 403. Returning empty to save time.
    # Manual paste is the recommended method for Trustpilot reviews.
    return pd.DataFrame(columns=["source", "product", "rating", "text", "date"])


def search_reddit(product_name: str) -> List[Dict]:
    """
    Searches Reddit for discussions using DuckDuckGo to ensure stability.
    """
    results = []
    # Broaden query to find any relevant discussion
    query = f'site:reddit.com "{product_name}"'
    search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    try:
        with httpx.Client(headers=headers, timeout=15, follow_redirects=True) as client:
            resp = client.get(search_url)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")
                # DDG results often in result class
                items = soup.find_all('div', class_=re.compile(r'result|links_main'))[:5]
                
                for item in items:
                    title_el = item.find(['a', 'h2'], class_=re.compile(r'result__a|result__title'))
                    snippet_el = item.find('a', class_=re.compile(r'result__snippet'))
                    
                    if title_el and snippet_el:
                        title = title_el.get_text(strip=True)
                        snippet = snippet_el.get_text(strip=True)
                        results.append({
                            "source": "Reddit",
                            "text": f"{title}: {snippet}",
                            "rating": 0, # Reddit doesn't have 1-5 ratings usually
                            "url": title_el.get('href') if title_el.name == 'a' else title_el.find('a')['href']
                        })
    except Exception as e:
        print(f"Reddit search failed: {e}")
        
    return results


def search_youtube_videos(product_name: str, limit: int = 5) -> List[str]:
    try:
        query = f"{product_name} review".replace(" ", "+")
        url = f"https://www.youtube.com/results?search_query={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with httpx.Client(headers=headers, timeout=10) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                vids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", resp.text)
                unique_vids = []
                for v in vids:
                    if v not in unique_vids:
                        unique_vids.append(v)
                print(f"  [YouTube] Found {len(unique_vids)} videos for '{product_name}'")
                return unique_vids[:limit]
    except Exception as e:
        print(f"  [YouTube] Search error: {e}")
    return []


def _fetch_youtube_description(video_id: str) -> str:
    """Fetch the video description from the YouTube watch page (no API key needed)."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers=headers,
            timeout=10,
        )
        m = re.search(r'"shortDescription":"(.*?)","isCrawlable"', resp.text, re.DOTALL)
        if m:
            return (
                m.group(1)
                .replace("\\n", " ")
                .replace('\\"', '"')
                .replace("\\u0026", "&")
                .replace("\\u003c", "<")
                .replace("\\u003e", ">")
                [:2500]
            )
    except Exception:
        pass
    return ""


def load_youtube_reviews(product_name: str, video_ids: List[str]) -> List[Dict]:
    cache_dir = "data/cache"
    os.makedirs(cache_dir, exist_ok=True)

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        reviews = []
        for vid in video_ids:
            cache_path = os.path.join(cache_dir, f"{vid}.txt")

            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    text = f.read()
                print(f"  [YouTube] Loaded {vid} from local cache.")
                reviews.append({
                    "source": "YouTube",
                    "product": product_name,
                    "rating": 3.5,
                    "text": text,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                })
                continue

            try:
                print(f"  [YouTube] Loading transcript for {vid}...")
                transcript = YouTubeTranscriptApi().fetch(vid)
                text = " ".join(t.text for t in transcript)[:2500]
                if len(text) > 50:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        f.write(text)
                    reviews.append({
                        "source": "YouTube",
                        "product": product_name,
                        "rating": 3.5,
                        "text": text,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                    })
                    print(f"    - Success: {len(text)} chars.")
            except Exception as e:
                err_msg = str(e)
                if "IP has been blocked" in err_msg or "too many requests" in err_msg.lower():
                    print(f"    - Rate-limited. Falling back to video description for {vid}...")
                    text = _fetch_youtube_description(vid)
                    if len(text) > 50:
                        with open(cache_path, "w", encoding="utf-8") as f:
                            f.write(text)
                        reviews.append({
                            "source": "YouTube",
                            "product": product_name,
                            "rating": 3.5,
                            "text": text,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                        })
                        print(f"    - Got description: {len(text)} chars.")
                    else:
                        print(f"    - Description also unavailable for {vid}.")
                else:
                    print(f"    - Error: {e}")
        return reviews
    except Exception:
        return []


def load_amazon_reviews_web(product_name: str, limit: int = 20) -> List[Dict]:
    try:
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        q = requests.utils.quote(product_name)
        resp = requests.get(f"https://www.amazon.com/s?k={q}", headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "lxml")

        asin = None
        for a in soup.select("a[href*='/dp/']"):
            m = re.search(r"/dp/([A-Z0-9]{10})", a.get("href", ""))
            if m:
                asin = m.group(1)
                break
        if not asin:
            return []

        resp = requests.get(
            f"https://www.amazon.com/product-reviews/{asin}?reviewerType=all_reviews",
            headers=headers,
            timeout=10,
        )
        soup = BeautifulSoup(resp.text, "lxml")
        reviews = []
        for card in soup.select("[data-hook='review']")[:limit]:
            text_el = card.select_one("[data-hook='review-body'] span")
            rating_el = card.select_one("[data-hook='review-star-rating'] span.a-icon-alt")
            date_el = card.select_one("[data-hook='review-date']")

            text = text_el.get_text(strip=True) if text_el else ""
            if not text:
                continue

            rating = 3.0
            if rating_el:
                try:
                    rating = float(rating_el.get_text().split()[0])
                except (ValueError, IndexError):
                    pass

            date = datetime.now().strftime("%Y-%m-%d")
            if date_el:
                m = re.search(r"(\w+ \d+, \d{4})", date_el.get_text())
                if m:
                    try:
                        date = datetime.strptime(m.group(1), "%B %d, %Y").strftime("%Y-%m-%d")
                    except ValueError:
                        pass

            reviews.append({
                "source": "Amazon",
                "product": product_name,
                "rating": rating,
                "text": text,
                "date": date,
            })
        return reviews
    except Exception:
        return []


def load_bestbuy_reviews_web(product_name: str, limit: int = 20) -> List[Dict]:
    try:
        q = requests.utils.quote(product_name)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        # Search BestBuy to find the product SKU
        resp = requests.get(
            f"https://www.bestbuy.com/site/searchpage.jsp?st={q}",
            headers=headers,
            timeout=10,
        )
        sku_m = re.search(r'"sku"\s*:\s*"?(\d{7,})"?', resp.text)
        if not sku_m:
            return []
        sku = sku_m.group(1)

        # Fetch reviews from BestBuy's UGC reviews API
        rev_resp = requests.get(
            f"https://www.bestbuy.com/ugc/v2/reviews"
            f"?page=1&pageSize={limit}&subject={sku}&sort=MOST_HELPFUL",
            headers={**headers, "Accept": "application/json"},
            timeout=10,
        )
        data = rev_resp.json()
        reviews = []
        for r in data.get("reviews", [])[:limit]:
            text = r.get("text", "") or r.get("title", "")
            if not text:
                continue
            reviews.append({
                "source": "BestBuy",
                "product": product_name,
                "rating": float(r.get("rating", 3.0)),
                "text": text,
                "date": str(r.get("submissionTime", datetime.now().strftime("%Y-%m-%d")))[:10],
            })
        return reviews
    except Exception:
        return []


def collect_reviews(
    product_name: str,
    pasted_reviews: Optional[str] = None,
    youtube_ids: Optional[List[str]] = None,
) -> List[Dict]:
    from concurrent.futures import ThreadPoolExecutor

    all_reviews: List[Dict] = []

    if pasted_reviews:
        all_reviews.extend(load_pasted_reviews(pasted_reviews, product_name))

    local_data = load_file_reviews(product_name)
    all_reviews.extend(local_data)

    if not youtube_ids:
        youtube_ids = search_youtube_videos(product_name)

    need_amazon = not any(r["source"] == "Amazon" for r in all_reviews)
    need_bestbuy = not any(r["source"] == "BestBuy" for r in all_reviews)

    # Run all three web scrapers concurrently
    with ThreadPoolExecutor(max_workers=3) as pool:
        yt_future = pool.submit(load_youtube_reviews, product_name, youtube_ids or [])
        az_future = pool.submit(load_amazon_reviews_web, product_name) if need_amazon else None
        bb_future = pool.submit(load_bestbuy_reviews_web, product_name) if need_bestbuy else None

        yt_reviews = yt_future.result()
        az_reviews = az_future.result() if az_future else []
        bb_reviews = bb_future.result() if bb_future else []

    all_reviews.extend(yt_reviews)
    all_reviews.extend(az_reviews)
    all_reviews.extend(bb_reviews)

    return all_reviews
