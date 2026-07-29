from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from faster_whisper import WhisperModel

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

#to start:uvicorn server:app --host 0.0.0.0 --port 8000