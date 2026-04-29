import sys
sys.path.append('backend')
from routers.analyze import analyze_product
from models import AnalyzeRequest, Preferences
import asyncio

async def test():
    req = AnalyzeRequest(
        product_name="Fake Obscure Product 101",
        preferences=Preferences(
            budget="mid",
            use_case="gaming",
            aspect_priorities={},
            deal_breakers=[]
        )
    )
    res = await analyze_product(req)
    print("Pros:", res.pros)
    print("Cons:", res.cons)
    print("Evidence Count:", len(res.evidence))
    if len(res.evidence) > 0:
        print("First Evidence:", res.evidence[0])

asyncio.run(test())
