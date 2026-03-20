"""Web UI用FastAPIアプリケーション"""

from __future__ import annotations

import asyncio
import json
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse

from book2audio.web.pipeline import Job, Phase, jobs, run_pipeline

app = FastAPI(title="book2audio")

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)


@app.post("/api/convert")
async def convert(
    file: UploadFile,
    voice: str = Form("ja-JP-NanamiNeural"),
    rate: str = Form("+0%"),
    dpi: int = Form(300),
    pages: str = Form(""),
    remove_ruby: bool = Form(True),
):
    job_id = uuid.uuid4().hex[:12]
    output_dir = tempfile.mkdtemp(prefix=f"book2audio_{job_id}_")

    # PDFをtemp dirに保存
    pdf_path = Path(output_dir) / "input.pdf"
    pdf_path.write_bytes(await file.read())

    jobs[job_id] = Job(output_dir=output_dir)

    asyncio.create_task(run_pipeline(
        job_id=job_id,
        pdf_path=str(pdf_path),
        output_dir=output_dir,
        voice=voice,
        rate=rate,
        dpi=dpi,
        pages=pages if pages else None,
        remove_ruby=remove_ruby,
    ))

    return {"job_id": job_id}


@app.get("/api/progress/{job_id}")
async def progress(job_id: str):
    if job_id not in jobs:
        return StreamingResponse(
            iter([f"data: {json.dumps({'phase': 'error', 'message': 'Job not found'})}\n\n"]),
            media_type="text/event-stream",
        )

    job = jobs[job_id]

    async def event_stream():
        while True:
            event = await job.queue.get()
            data = {
                "phase": event.phase,
                "current": event.current,
                "total": event.total,
                "message": event.message,
            }
            if event.phase == Phase.done:
                data["files"] = job.files
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            if event.phase in (Phase.done, Phase.error):
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/download/{job_id}/{filename}")
async def download(job_id: str, filename: str):
    if job_id not in jobs:
        return {"error": "Job not found"}
    job = jobs[job_id]
    filepath = Path(job.output_dir) / "audio" / filename
    if not filepath.exists():
        return {"error": "File not found"}
    return FileResponse(filepath, filename=filename, media_type="audio/mpeg")


def start():
    import uvicorn
    uvicorn.run(
        "book2audio.web.app:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )


if __name__ == "__main__":
    start()
