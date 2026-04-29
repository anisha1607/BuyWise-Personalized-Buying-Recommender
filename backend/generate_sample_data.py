import pandas as pd
import json
import random
import os
from datetime import datetime, timedelta

PRODUCTS = [
    "Sony WH-1000XM5",
    "Bose QuietComfort 45",
    "Apple MacBook Pro 14",
    "Apple AirPods Pro 2",
    "Samsung Galaxy S23",
    "Dell XPS 15",
    "Jabra Evolve2 85",
    "Anker Soundcore Q45",
    "Beats Studio Pro",
    "Sennheiser Momentum 4",
]

POSITIVE = {
    "comfort": [
        "The ear cups are incredibly soft and I can wear these for hours without discomfort.",
        "Surprisingly comfortable even during long sessions, the headband doesn't dig in at all.",
        "The ergonomic design makes these feel almost weightless on my head.",
        "Perfect fit right out of the box, the padding is plush and luxurious.",
        "I wore these on a 12-hour flight and my ears felt completely fine throughout.",
    ],
    "price": [
        "Worth every single penny, the value you get is truly outstanding.",
        "Expensive upfront but the quality completely justifies the cost.",
        "Found these on sale and they're an absolute steal at that price point.",
        "Premium price but you're paying for premium quality, absolutely no regrets.",
        "Compared to competitors, the price-to-performance ratio here is excellent.",
    ],
    "battery": [
        "Battery life is absolutely incredible, lasts way longer than advertised.",
        "Charged once and used them for three full days without needing a top-up.",
        "The quick charge feature is a lifesaver — 15 minutes gives several hours of playback.",
        "30+ hours of battery is not a marketing gimmick, it actually delivers every time.",
        "Battery management is smart and the drain is minimal even in high-usage modes.",
    ],
    "sound": [
        "The audio quality is simply stunning, every instrument is crystal clear.",
        "Bass response is deep and satisfying without being muddy or overpowering at all.",
        "The soundstage is wide and immersive, feels like you're at a live concert.",
        "Balanced frequency response makes these great for all genres of music.",
        "The detail retrieval is exceptional, I'm hearing things in songs I never noticed before.",
    ],
    "durability": [
        "Built like a tank, feels like it will last for years with proper care.",
        "Premium materials throughout, nothing feels cheap or plasticky whatsoever.",
        "Survived being dropped multiple times without any damage or rattles.",
        "The hinge mechanism feels incredibly solid and the build quality is top notch.",
        "Six months of heavy daily use and it still looks and performs like brand new.",
    ],
    "performance": [
        "The noise cancellation is best-in-class, blocks out absolutely everything around me.",
        "Performance in calls is excellent, colleagues always say my voice sounds clear.",
        "The processing is fast and responsive, no lag or latency issues whatsoever.",
        "Handles multitasking beautifully without any slowdowns or hiccups at all.",
        "The ANC algorithm is incredibly smart and adapts automatically to your environment.",
    ],
    "design": [
        "The sleek minimalist design looks absolutely premium and professional.",
        "Aesthetics are gorgeous, gets compliments everywhere I use them.",
        "The matte finish resists fingerprints and looks clean all day long.",
        "Compact foldable design makes it very easy to travel with anywhere.",
        "The color options are tasteful and the overall look is very refined and elegant.",
    ],
    "connectivity": [
        "Bluetooth pairing is instant and rock solid, never drops the connection.",
        "Multipoint pairing works flawlessly between my laptop, phone, and tablet simultaneously.",
        "The wireless range is impressive, stays connected even from across the house.",
        "USB-C connectivity is a huge plus for both charging and wired use.",
        "NFC pairing is super convenient and just works perfectly every single time.",
    ],
}

NEGATIVE = {
    "comfort": [
        "The clamping force is way too tight and causes headaches after just an hour.",
        "Ear cups are too small for larger ears and start to feel very painful over time.",
        "The headband digs into my skull during longer listening sessions.",
        "After two hours my ears get hot and sweaty from the overly tight seal.",
        "The weight is uncomfortable and causes noticeable neck fatigue during long use.",
    ],
    "price": [
        "Way too expensive for what you actually get, feels completely overpriced.",
        "The premium price tag is simply not justified given the quality issues I experienced.",
        "Better options available for half the price if you look around a bit.",
        "Price gouging at its finest, the margins here must be absolutely enormous.",
        "Not worth the premium when budget alternatives perform remarkably similarly.",
    ],
    "battery": [
        "Battery life is much shorter than advertised, barely lasts 6 hours on a charge.",
        "The battery drains surprisingly quickly even when the device is not in active use.",
        "Charging takes way too long compared to what competitors are offering.",
        "Battery health degrades noticeably after just a few months of normal use.",
        "The standby drain is terrible, loses significant charge just sitting on the desk.",
    ],
    "sound": [
        "The bass is completely overpowering and muddy, drowning out the mids and highs.",
        "Treble is harsh and fatiguing for extended listening sessions.",
        "The soundstage feels narrow and closed-in, lacks depth and spatial awareness.",
        "Audio quality at high volumes degrades noticeably and introduces distortion.",
        "The EQ preset options are severely limited and the default tuning is quite poor.",
    ],
    "durability": [
        "The build quality feels cheap and plasticky for such a high price point.",
        "The hinge cracked after just a few months of completely normal everyday use.",
        "The ear cushions started peeling and deteriorating within the first year.",
        "Feels fragile and like it could break with any significant accidental impact.",
        "The cable port is already loose and connection issues started very early on.",
    ],
    "performance": [
        "The noise cancellation is quite underwhelming and lets in a lot of ambient sound.",
        "Microphone quality on calls is poor and people consistently struggle to hear me.",
        "Performance degrades noticeably when multiple applications are running.",
        "The ANC creates an uncomfortable pressure sensation that gives me headaches.",
        "Software is buggy and requires constant updates just to fix basic issues.",
    ],
    "design": [
        "The design looks dated and generic compared to virtually all the competition.",
        "The glossy finish is a constant fingerprint magnet and looks dirty all the time.",
        "The folding mechanism feels quite flimsy and I worry about long-term reliability.",
        "The color options are boring and completely uninspired, needs far more variety.",
        "Bulky and unflattering design, makes you look ridiculous wearing them in public.",
    ],
    "connectivity": [
        "Bluetooth connection drops frequently and requires constant annoying reconnecting.",
        "Multipoint pairing is unreliable and switches devices completely unexpectedly.",
        "The wireless range is poor, drops connection beyond just 10 feet away.",
        "Pairing process is overly complicated and genuinely frustrating to set up initially.",
        "NFC pairing is very hit or miss, sometimes works fine, sometimes just doesn't.",
    ],
}


def generate_review_text(sentiment_bias: str) -> str:
    aspects = list(POSITIVE.keys())
    selected = random.sample(aspects, random.randint(2, 4))
    sentences = []
    for aspect in selected:
        if sentiment_bias == "positive":
            pool = POSITIVE[aspect] if random.random() < 0.85 else NEGATIVE[aspect]
        elif sentiment_bias == "negative":
            pool = NEGATIVE[aspect] if random.random() < 0.80 else POSITIVE[aspect]
        else:
            pool = POSITIVE[aspect] if random.random() < 0.5 else NEGATIVE[aspect]
        sentences.append(random.choice(pool))
    return " ".join(sentences)


def random_date(start_year: int = 2020, end_year: int = 2024) -> str:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).strftime("%Y-%m-%d")


def pick_sentiment(weights=(0.65, 0.2, 0.15)) -> str:
    return random.choices(["positive", "mixed", "negative"], weights=weights)[0]


def sentiment_to_rating(s: str) -> int:
    if s == "positive":
        return random.choice([4, 4, 5, 5, 5])
    if s == "negative":
        return random.choice([1, 1, 2, 2, 3])
    return random.choice([3, 3, 4])


def build_rows(n: int, source: str, weights=(0.65, 0.2, 0.15), year_range=(2020, 2024)) -> list:
    rows = []
    for _ in range(n):
        product = random.choice(PRODUCTS)
        s = pick_sentiment(weights)
        rows.append({
            "source": source,
            "product": product,
            "rating": sentiment_to_rating(s),
            "text": generate_review_text(s),
            "date": random_date(*year_range),
            "title": f"{product} Review",
        })
    return rows


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    print("Generating Amazon reviews (500 rows)...")
    amazon = pd.DataFrame(build_rows(500, "amazon"))
    amazon.to_csv("data/amazon_reviews.csv", index=False)
    print(f"  Saved {len(amazon)} rows → data/amazon_reviews.csv")

    print("Generating BestBuy reviews (200 rows)...")
    bestbuy = pd.DataFrame(build_rows(200, "bestbuy", weights=(0.6, 0.25, 0.15)))
    bestbuy.to_csv("data/bestbuy_reviews.csv", index=False)
    print(f"  Saved {len(bestbuy)} rows → data/bestbuy_reviews.csv")

    print("Generating Amazon 2023 JSON (300 records)...")
    records = build_rows(300, "amazon", year_range=(2023, 2024))
    with open("data/amazon_reviews_2023.json", "w") as f:
        json.dump(records, f, indent=2)
    print(f"  Saved {len(records)} records → data/amazon_reviews_2023.json")

    print("\nDone! Sample data ready in data/")
