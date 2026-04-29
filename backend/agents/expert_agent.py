import httpx
import re
from bs4 import BeautifulSoup
from typing import List, Dict

def get_expert_reviews(product_name: str) -> List[Dict]:
    """
    Searches for professional reviews using multiple fallback selectors for robustness.
    """
    experts = []
    query = f"{product_name} professional review"
    # Use the standard DDG search which is often more reliable than the HTML one if headers are right
    search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://duckduckgo.com/"
    }

    try:
        with httpx.Client(headers=headers, timeout=15, follow_redirects=True) as client:
            resp = client.get(search_url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                # DDG HTML version uses 'result' class
                results = soup.find_all('div', class_=re.compile(r'result|links_main'))[:3]
                
                for res in results:
                    title_el = res.find(['a', 'h2'], class_=re.compile(r'result__a|result__title'))
                    snippet_el = res.find('a', class_=re.compile(r'result__snippet'))
                    
                    if title_el:
                        title = title_el.get_text(strip=True)
                        url = title_el.get('href') if title_el.name == 'a' else title_el.find('a')['href']
                        snippet = snippet_el.get_text(strip=True) if snippet_el else "Professional review available."
                        
                        if not url.startswith('http'): continue # Skip relative links
                        
                        source = "Expert Review"
                        for domain in ["theverge", "techradar", "rtings", "cnet", "tomsguide", "digitaltrends", "engadget", "wired"]:
                            if domain in url.lower():
                                source = domain.capitalize().replace("tomsguide", "Tom's Guide")
                        
                        experts.append({"source": source, "title": title, "url": url, "snippet": snippet})
    except Exception as e:
        print(f"Expert search failed: {e}")

    return experts

def get_tiktok_links(product_name: str) -> List[Dict]:
    """
    Finds TikTok links using a robust regex search on the search results page.
    """
    links = []
    query = f"{product_name} unboxing tiktok"
    search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}

    try:
        with httpx.Client(headers=headers, timeout=15) as client:
            resp = client.get(search_url)
            if resp.status_code == 200:
                # Direct regex search on raw HTML is more reliable for social links
                matches = re.findall(r"tiktok\.com/@[a-zA-Z0-9._-]+/video/[0-9]+", resp.text)
                for m in list(set(matches))[:4]:
                    links.append({"url": f"https://{m}", "label": "Watch Unboxing"})
    except Exception:
        pass
    
    return links
