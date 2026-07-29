from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from faster_whisper import WhisperModel

app = FastAPI(title="Local Whisper API")

# Für CPU geeignet:
MODEL_NAME = "base"

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


@app.post("/transcribe")
async def transcribe(
    audio: Annotated[UploadFile, File(...)],
) -> dict:
    if audio.content_type:
        print("Content-Type:", audio.content_type)

    suffix = Path(audio.filename or "audio.mp3").suffix or ".mp3"

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