import os
import json
import re
import httpx
import urllib.parse
from typing import List, Dict, Optional
from datetime import datetime

# [NO LOCAL DATA POLICY] Removed load_file_reviews to prevent usage of precomputed/mock CSV/JSON files.

def load_pasted_reviews(text: str, product_name: str) -> List[Dict]:
    """
    Splits pasted text into manageable snippets and treats them as personal reviews.
    """
    # Simple split by paragraph or double newline
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    results = []
    for i, p in enumerate(paragraphs):
        results.append({
            "source": "Personal",
            "source_name": "Personal",
            "source_type": "Personal",
            "url": "",
            "title": f"Pasted Text {i+1}",
            "text": p,
            "rating": 3, # Default neutral rating, sentiment agent will refine this
            "product": product_name,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
    return results


# [NO LOCAL DATA POLICY] Trustpilot loading removed.


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
                        link = title_el.get('href') if title_el.name == 'a' else title_el.find('a')['href']
                        results.append({
                            "source": "Reddit",
                            "source_name": "Reddit",
                            "source_type": "Forum",
                            "url": link,
                            "title": title,
                            "text": f"{title}: {snippet}",
                            "rating": 0, # Reddit doesn't have 1-5 ratings usually
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
        with httpx.Client(headers=headers, timeout=10) as client:
            resp = client.get(f"https://www.youtube.com/watch?v={video_id}")
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
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        reviews = []
        transcripts_blocked = False
        for vid in video_ids:
            try:
                if transcripts_blocked:
                    raise Exception("Transcripts blocked for this session.")
                print(f"  [YouTube] Loading transcript for {vid}...")
                transcript = YouTubeTranscriptApi().fetch(vid)
                text = " ".join(t.text for t in transcript)[:2500]
                if len(text) > 50:
                    reviews.append({
                        "source": "YouTube",
                        "source_name": "YouTube",
                        "source_type": "Video",
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "title": f"Video Review ({vid})",
                        "product": product_name,
                        "rating": 3.5,
                        "text": text,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                    })
                    print(f"    - Success: {len(text)} chars.")
            except Exception as e:
                err_msg = str(e)
                if "IP has been blocked" in err_msg or "too many requests" in err_msg.lower() or transcripts_blocked:
                    transcripts_blocked = True
                    print(f"    - Rate-limited. Falling back to video description for {vid}...")
                    text = _fetch_youtube_description(vid)
                    if len(text) > 50:
                        reviews.append({
                            "source": "YouTube",
                            "source_name": "YouTube",
                            "source_type": "Video",
                            "url": f"https://www.youtube.com/watch?v={vid}",
                            "title": f"Video Review ({vid})",
                            "product": product_name,
                            "rating": 3.5,
                            "text": text,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                        })
                        print(f"    - Got description: {len(text)} chars.")
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
        q = urllib.parse.quote(product_name)
        with httpx.Client(headers=headers, timeout=15, follow_redirects=True) as client:
            resp = client.get(f"https://www.amazon.com/s?k={q}")
            soup = BeautifulSoup(resp.text, "lxml")

            asin = None
            for a in soup.select("a[href*='/dp/']"):
                m = re.search(r"/dp/([A-Z0-9]{10})", a.get("href", ""))
                if m:
                    asin = m.group(1)
                    break
            if not asin:
                return []

            resp = client.get(f"https://www.amazon.com/product-reviews/{asin}?reviewerType=all_reviews")
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
                    "source_name": "Amazon",
                    "source_type": "Retailer",
                    "url": f"https://www.amazon.com/dp/{asin}",
                    "title": "",
                    "product": product_name,
                    "rating": rating,
                    "text": text,
                    "date": date,
                })
            return reviews
    except Exception as e:
        print(f"  [Amazon] Scrape error: {e}")
        return []


def load_bestbuy_reviews_web(product_name: str, limit: int = 20) -> List[Dict]:
    try:
        q = urllib.parse.quote(product_name)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        with httpx.Client(headers=headers, timeout=15, follow_redirects=True) as client:
            # Search BestBuy to find the product SKU
            resp = client.get(f"https://www.bestbuy.com/site/searchpage.jsp?st={q}")
            sku_m = re.search(r'"sku"\s*:\s*"?(\d{7,})"?', resp.text)
            if not sku_m:
                return []
            sku = sku_m.group(1)

            # Fetch reviews from BestBuy's UGC reviews API
            rev_resp = client.get(
                f"https://www.bestbuy.com/ugc/v2/reviews"
                f"?page=1&pageSize={limit}&subject={sku}&sort=MOST_HELPFUL",
                headers={"Accept": "application/json"}
            )
            data = rev_resp.json()
            reviews = []
            for r in data.get("reviews", [])[:limit]:
                text = r.get("text", "") or r.get("title", "")
                if not text:
                    continue
                reviews.append({
                    "source": "BestBuy",
                    "source_name": "BestBuy",
                    "source_type": "Retailer",
                    "url": f"https://www.bestbuy.com/site/{sku}.p",
                    "title": r.get("title", ""),
                    "product": product_name,
                    "rating": float(r.get("rating", 3.0)),
                    "text": text,
                    "date": str(r.get("submissionTime", datetime.now().strftime("%Y-%m-%d")))[:10],
                })
            return reviews
    except Exception as e:
        print(f"  [BestBuy] Scrape error: {e}")
        return []


def _search_reviews_ddg(product_name: str, site: str, source_label: str, limit: int = 5) -> List[Dict]:
    """
    Fallback: search DuckDuckGo for review snippets from a specific site.
    Used when direct scraping fails (anti-bot blocks, CAPTCHAs, etc.)
    """
    results = []
    import random, time
    query = f'site:{site} "{product_name}" review'
    search_url = f"https://duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
    
    time.sleep(random.uniform(1.0, 2.5)) # Slightly longer delay
    
    print(f"  [{source_label}] Attempting DDG Lite Fallback: {search_url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://duckduckgo.com/",
    }

    try:
        with httpx.Client(headers=headers, timeout=15.0, follow_redirects=True) as client:
            resp = client.get(search_url)
            if resp.status_code in (200, 202):  # 202 = DDG bot-detection soft-block; body may still have results
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "lxml")

                # DDG Lite uses table rows for results
                # Usually: <td class="result-title">, <td class="result-snippet">
                rows = soup.find_all('tr')
                
                for i in range(len(rows)):
                    row = rows[i]
                    # Title is usually in an 'a' inside a 'td'
                    title_a = row.find('a', class_='result-link')
                    if not title_a: continue
                    
                    # Snippet is often in the NEXT row for Lite version, or same row
                    snippet = ""
                    snippet_td = row.find('td', class_='result-snippet')
                    if snippet_td:
                        snippet = snippet_td.get_text(strip=True)
                    elif i + 1 < len(rows):
                        # Fallback: check next row
                        next_row_text = rows[i+1].get_text(strip=True)
                        if len(next_row_text) > 40 and "result-link" not in str(rows[i+1]):
                            snippet = next_row_text
                    
                    if title_a and len(snippet) > 15:
                        title = title_a.get_text(strip=True)
                        link = title_a.get('href', "")
                        if "http" not in link and link.startswith("//"):
                            link = "https:" + link
                        
                        results.append({
                            "source": source_label,
                            "source_name": source_label,
                            "source_type": "Retailer" if source_label in ("Amazon", "BestBuy") else "Web",
                            "url": link,
                            "title": title,
                            "text": f"{title}: {snippet}",
                            "product": product_name,
                            "rating": 3.5,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                        })
                        if len(results) >= limit: break
            else:
                print(f"  [{source_label}] DDG Lite failed (Status {resp.status_code})")
    except Exception as e:
        print(f"  [{source_label}] DDG fallback error: {e}")
        
    print(f"  [{source_label}] DDG fallback found {len(results)} results")
    return results


def collect_reviews(
    product_name: str,
    pasted_reviews: Optional[str] = None,
    youtube_ids: Optional[List[str]] = None,
) -> List[Dict]:
    from concurrent.futures import ThreadPoolExecutor

    all_reviews: List[Dict] = []

    if pasted_reviews:
        all_reviews.extend(load_pasted_reviews(pasted_reviews, product_name))

    # [NO LOCAL DATA POLICY] Removed load_file_reviews call to ensure every analysis is live.

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

    # Fallback: if Amazon or BestBuy direct scraping failed, try DuckDuckGo search
    has_amazon = any(r.get("source") == "Amazon" for r in all_reviews)
    has_bestbuy = any(r.get("source") == "BestBuy" for r in all_reviews)
    
    if not has_amazon:
        print("  [Amazon] Direct scrape returned 0 results, trying DDG fallback...")
        all_reviews.extend(_search_reviews_ddg(product_name, "amazon.com", "Amazon"))
    
    if not has_bestbuy:
        print("  [BestBuy] Direct scrape returned 0 results, trying DDG fallback...")
        all_reviews.extend(_search_reviews_ddg(product_name, "bestbuy.com", "BestBuy"))

    return all_reviews
