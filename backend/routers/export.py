import io
import csv
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from models import ExportRequest

router = APIRouter()


@router.post("/export")
async def export_data(request: ExportRequest):
    if request.format == "json":
        content = json.dumps(request.data, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=buywise_analysis.json"},
        )

    if request.format == "csv":
        out = io.StringIO()
        w = csv.writer(out)

        w.writerow(["Product", "Fit Score", "Review Count", "Verdict"])
        w.writerow([
            request.data.get("product", ""),
            request.data.get("fit_score", ""),
            request.data.get("review_count", ""),
            request.data.get("verdict", ""),
        ])
        w.writerow([])

        w.writerow(["Aspect", "Avg Sentiment", "Mention Count"])
        for aspect, d in request.data.get("aspect_summary", {}).items():
            w.writerow([aspect, d.get("avg_sentiment", ""), d.get("mention_count", "")])
        w.writerow([])

        w.writerow(["Source", "Avg Sentiment", "Review Count"])
        for src, d in request.data.get("source_comparison", {}).items():
            w.writerow([src, d.get("avg_sentiment", ""), d.get("review_count", "")])

        return StreamingResponse(
            io.BytesIO(out.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=buywise_analysis.csv"},
        )

    return JSONResponse({"error": "Invalid format. Use 'json' or 'csv'."}, status_code=400)
