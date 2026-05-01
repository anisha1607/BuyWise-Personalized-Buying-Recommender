import re

with open("backend/routers/analyze.py", "r") as f:
    content = f.read()

# We'll replace the generate_market_consensus function with _run_llm_enrichment_fallback

# Wait, instead of a regex replace, let's just create the new function at the module level.
