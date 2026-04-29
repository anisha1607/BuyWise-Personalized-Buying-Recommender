import sys
sys.path.append('backend')
from agents.eda_agent import source_comparison, detect_contradictions

reviews = [
    {"source_name": "Amazon", "rating": 5.0},
    {"source_name": "Amazon", "rating": 4.0},
    {"source": "amazon", "rating": 3.0}, # Should map to Amazon
    {"source": "bestbuy", "rating": 1.0}, # Should map to BestBuy
    {"source_name": "YouTube", "rating": 5.0},
    {"source_name": "Reddit", "rating": 3.5},
]

print(source_comparison(reviews, {}))

aspect_summary = {
    "Battery Life": {
        "snippets": [
            {"text": "Love the battery", "score": 0.5},
            {"text": "Battery lasts forever", "score": 0.8},
            {"text": "Battery dies fast", "score": -0.5},
            {"text": "Awful battery life", "score": -0.6},
        ]
    },
    "Comfort": {
        "snippets": [
            {"text": "Super comfy", "score": 0.5},
            {"text": "Very comfortable", "score": 0.8},
            {"text": "A bit tight", "score": -0.2},
        ]
    }
}
print("\nContradictions:")
print(detect_contradictions(aspect_summary))
