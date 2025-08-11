import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
import yaml
import io
import subprocess
import logging
from datetime import datetime
import json
from audio_utils import convert_audio_ffmpeg, get_audio_duration_ffprobe
import sys
import argparse

# Load configuration from config.yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

UPLOAD_DIR = config.get("upload_dir", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
TRANSCRIPTIONS_DIR = config.get("transcriptions_dir", "transcriptions")
os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)

# Setup logging
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

app = FastAPI()

def convert_audio(input_bytes: bytes, input_format: str, output_format: str = "wav", sample_width: int = 2, channels: int = 1, frame_rate: int = 16000) -> bytes:
    return convert_audio_ffmpeg(input_bytes, input_format, output_format, sample_width, channels, frame_rate)

# Add whisper.cpp config loading
def get_whisper_config():
    whisper_cfg = config.get("whisper", {})
    exe_path = whisper_cfg.get("exe_path", "./whisper.cpp/main")
    model_path = whisper_cfg.get("model_path", "./models/ggml-base.en.bin")
    extra_args = whisper_cfg.get("extra_args", "")
    return exe_path, model_path, extra_args

def transcribe_with_whisper(audio_path: str, transcript_name: str) -> str:
    exe_path, model_path, extra_args = get_whisper_config()
    exe_path = os.path.expanduser(exe_path)
    model_path = os.path.expanduser(model_path)
    transcript_path = os.path.join(TRANSCRIPTIONS_DIR, transcript_name)
    cmd = [exe_path, "-m", model_path, "-f", audio_path, "-otxt", "-of", transcript_path]
    if extra_args:
        cmd += extra_args.split()
    logging.info(f"Running whisper.cpp: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logging.info(f"whisper.cpp stdout: {result.stdout}")
        logging.info(f"whisper.cpp stderr: {result.stderr}")
        txt_path = transcript_path + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r") as f:
                return f.read()
        else:
            logging.error("No transcript file found at %s", txt_path)
            return "(No transcript file found)"
    except Exception as e:
        logging.exception(f"Transcription error: {e}")
        return f"(Transcription error: {e})"

@app.post("/upload-audio")
async def upload_audio(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    input_bytes = await file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    input_format = ext.lstrip('.')
    # Extract source from header
    source = request.headers.get("source", "unknown") if request else "unknown"
    # Get audio length from original file
    audio_length_sec = round(get_audio_duration_ffprobe(input_bytes, input_format), 2)
    file_size = len(input_bytes)
    # Save original file (archive)
    original_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(original_path, "wb") as buffer:
        buffer.write(input_bytes)
    # Convert to wav for whisper.cpp
    if input_format == "m4a":
        output_bytes = convert_audio(input_bytes, input_format="m4a", output_format="wav", sample_width=2, channels=1, frame_rate=16000)
        save_name = os.path.splitext(file.filename)[0] + ".wav"
    elif input_format == "mp4":
        # Extract audio from mp4 video
        output_bytes = convert_audio(input_bytes, input_format="mp4", output_format="wav", sample_width=2, channels=1, frame_rate=16000)
        save_name = os.path.splitext(file.filename)[0] + ".wav"
    else:
        output_bytes = input_bytes
        save_name = file.filename
    wav_path = os.path.join(UPLOAD_DIR, save_name)
    with open(wav_path, "wb") as buffer:
        buffer.write(output_bytes)
    # Transcribe
    transcript_name = os.path.splitext(file.filename)[0]
    exe_path, model_path, extra_args = get_whisper_config()
    meta = {
        "datetime": datetime.utcnow().isoformat() + "Z",
        "source": source,
        "original_filename": file.filename,
        "audio_length_sec": audio_length_sec,
        "file_size": file_size,
        "whisper_model": model_path,
        "whisper_args": extra_args,
        "status": "processing",
        "error": None,
        "language": None,
        "transcription_text": None
    }
    # Save JSON metadata
    json_path = os.path.join(TRANSCRIPTIONS_DIR, transcript_name + ".json")
    with open(json_path, "w") as jf:
        json.dump(meta, jf, ensure_ascii=False, indent=2)
    def background_transcribe():
        transcript = transcribe_with_whisper(wav_path, transcript_name)
        if os.path.exists(wav_path) and wav_path != original_path:
            os.remove(wav_path)
        meta["status"] = "success" if transcript and not transcript.startswith("(") else "error"
        meta["error"] = None if transcript and not transcript.startswith("(") else transcript
        meta["transcription_text"] = transcript
        # Save after transcription
        with open(json_path, "w") as jf:
            json.dump(meta, jf, ensure_ascii=False, indent=2)
        # --- Automated LLM Markdown Polishing ---
        try:
            from ollama_client import OllamaClient
            import logging
            logging.basicConfig(filename="server.log", level=logging.INFO)
            if transcript and meta["status"] == "success":
                client = OllamaClient()
                llm_result = client.generate_markdown(transcript)
                import json as _json
                # Parse if string
                if isinstance(llm_result, str):
                    try:
                        llm_result = _json.loads(llm_result)
                    except Exception:
                        llm_result = {"markdown": llm_result, "title": "", "file_name": ""}
                md_content = llm_result.get("markdown", "")
                md_title = llm_result.get("title", "")
                md_file_name = llm_result.get("file_name") or (transcript_name + ".md")
                md_path = os.path.join("markdowns", md_file_name)
                with open(md_path, "w") as mf:
                    mf.write(md_content)
                meta["markdown_file"] = md_file_name
                if md_title:
                    meta["markdown_title"] = md_title
                with open(json_path, "w") as jf:
                    json.dump(meta, jf, ensure_ascii=False, indent=2)
                logging.info(f"[LLM MARKDOWN] Saved {md_file_name} for {transcript_name}")
        except Exception as e:
            try:
                with open("server.log", "a") as logf:
                    logf.write(f"[LLM ERROR] {transcript_name}: {e}\n")
            except Exception:
                pass
    if background_tasks is not None:
        background_tasks.add_task(background_transcribe)
    return JSONResponse(content={"status": "processing", "message": "Transcription started. Check the web UI for results.", "transcription_id": transcript_name})

def run_backend():
    import uvicorn
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    backend_cfg = config.get("backend_server", {"host": "0.0.0.0", "port": 8000})
    uvicorn.run("main:app", host=backend_cfg.get("host", "0.0.0.0"), port=backend_cfg.get("port", 8000))

def run_frontend():
    import uvicorn
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    frontend_cfg = config.get("frontend_server", {"host": "0.0.0.0", "port": 8001})
    uvicorn.run("webui:app", host=frontend_cfg.get("host", "0.0.0.0"), port=frontend_cfg.get("port", 8001))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Transcriber launcher")
    parser.add_argument("--backend", action="store_true", help="Run backend API server (main:app)")
    parser.add_argument("--frontend", action="store_true", help="Run frontend web UI (webui:app)")
    args = parser.parse_args()
    if args.backend:
        run_backend()
    elif args.frontend:
        run_frontend()
    else:
        print("Specify --backend or --frontend")
        sys.exit(1)
