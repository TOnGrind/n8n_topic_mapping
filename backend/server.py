from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated
import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from faster_whisper import WhisperModel

from io import BytesIO
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)






app = FastAPI(title="Local Whisper API")

# Für CPU geeignet:
MODEL_NAME = "medium"

model = WhisperModel(
    MODEL_NAME,
    device="cpu",
    compute_type="int8",
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": MODEL_NAME,
    }


from fastapi import FastAPI, Request

@app.post("/debug")
async def debug_request(request: Request):
    print("=== DEBUG REQUEST ===", flush=True)
    print("Methode:", request.method, flush=True)
    print("Content-Type:", request.headers.get("content-type"), flush=True)
    print("Headers:", dict(request.headers), flush=True)

    try:
        form = await request.form()

        print("Formularfelder:", list(form.keys()), flush=True)

        result = {}

        for key, value in form.multi_items():
            print(
                "Feld:",
                repr(key),
                "Typ:",
                type(value),
                flush=True,
            )

            if hasattr(value, "filename"):
                content = await value.read()

                print("Dateiname:", value.filename, flush=True)
                print("Dateityp:", value.content_type, flush=True)
                print("Größe:", len(content), flush=True)

                result[key] = {
                    "filename": value.filename,
                    "content_type": value.content_type,
                    "size": len(content),
                }
            else:
                print("Wert:", value, flush=True)
                result[key] = str(value)

        return {
            "success": True,
            "fields": result,
        }

    except Exception as error:
        print("Debug-Fehler:", repr(error), flush=True)

        body = await request.body()

        print("Raw Body Länge:", len(body), flush=True)
        print("Erste Bytes:", body[:200], flush=True)

        return {
            "success": False,
            "error": str(error),
            "content_type": request.headers.get("content-type"),
            "body_size": len(body),
        }

@app.post("/transcribe")
async def transcribe(
    audio:  UploadFile = File(...),
) -> dict:
    if audio.content_type:
        print("Content-Type:", audio.content_type)

    print("Content-Type:", audio.content_type)

    suffix = Path(audio.filename or "audio.mp3").suffix or ".mp3"
    print("=== Neue Anfrage ===")
    print("Dateiname:", audio.filename)
    print("Content-Type:", audio.content_type)
    print("Header:", audio.headers)
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = Path(temp_file.name)

            while chunk := await audio.read(1024 * 1024):
                temp_file.write(chunk)

        segments, info = model.transcribe(
            str(temp_path),
            language="de",
            beam_size=5,
            vad_filter=True,
        )

        segment_list = []
        full_text_parts = []

        for segment in segments:
            text = segment.text.strip()

            segment_list.append(
                {
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": text,
                }
            )

            if text:
                full_text_parts.append(text)

        return {
            "success": True,
            "filename": audio.filename,
            "language": info.language,
            "language_probability": round(info.language_probability, 4),
            "duration": round(info.duration, 2),
            "text": " ".join(full_text_parts),
            "segments": segment_list,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    finally:
        if "temp_path" in locals():
            temp_path.unlink(missing_ok=True)


class ServiceReport(BaseModel):
    kunde: Optional[str] = None
    einsatzdatum: Optional[str] = None
    techniker: Optional[str] = None
    einsatzort: Optional[str] = None
    problem: Optional[str] = None
    ziel: Optional[str] = None
    durchgefuehrte_arbeiten: Optional[str] = None
    verwendete_materialien: Optional[str] = None
    ergebnis: Optional[str] = None
    status: Optional[str] = None


def safe_value(value: Optional[str]) -> str:
    return value or "Nicht angegeben"


@app.post("/generate-pdf")
async def generate_pdf(report: ServiceReport):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Serviceprotokoll",
    )

    styles = getSampleStyleSheet()

    elements = [
        Paragraph("Serviceprotokoll", styles["Title"]),
        Spacer(1, 8 * mm),
    ]

    rows = [
        ["Kunde", safe_value(report.kunde)],
        ["Einsatzdatum", safe_value(report.einsatzdatum)],
        ["Techniker", safe_value(report.techniker)],
        ["Einsatzort", safe_value(report.einsatzort)],
        ["Problem", safe_value(report.problem)],
        ["Ziel", safe_value(report.ziel)],
        [
            "Durchgeführte Arbeiten",
            safe_value(report.durchgefuehrte_arbeiten),
        ],
        [
            "Verwendete Materialien",
            safe_value(report.verwendete_materialien),
        ],
        ["Ergebnis", safe_value(report.ergebnis)],
        ["Status", safe_value(report.status)],
    ]

    # Paragraph verhindert, dass lange Texte aus den Tabellenzellen laufen.
    table_data = [
        [
            Paragraph(str(label), styles["BodyText"]),
            Paragraph(str(value), styles["BodyText"]),
        ]
        for label, value in rows
    ]

    table = Table(
        table_data,
        colWidths=[55 * mm, 115 * mm],
        repeatRows=0,
    )

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, "#B8B8B8"),
                ("BACKGROUND", (0, 0), (0, -1), "#EEEEEE"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    elements.append(table)
    document.build(elements)

    buffer.seek(0)

    filename = "serviceprotokoll.pdf"

    buffer.seek(0)
    pdf_bytes = buffer.getvalue()

    response = requests.post(
        "http://localhost:3000/api/pdf-ready",
        data=pdf_bytes,
        headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
        timeout=30,
    )

    response.raise_for_status()

#to start:uvicorn server:app --host 0.0.0.0 --port 8000