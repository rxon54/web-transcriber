# Web Transcriber FastAPI Server

This project is a modular FastAPI server for audio/video transcription and post-processing. It supports:
- Audio/video file upload via POST (supports .m4a, .mp4, and more)
- Audio conversion to 16-bit mono 16kHz WAV for transcription
- Transcription using whisper.cpp (configurable via config.yaml)
- Saving original uploads, JSON metadata, and transcript text
- Web UI for browsing, viewing, and managing transcriptions
- Markdown generation from transcripts using an LLM (OpenAI API compatible)
- All directories and API/configs are set in config.yaml

## Features
- Accepts audio/video uploads via POST (`/upload-audio`)
- Converts audio/video to 16-bit mono 16kHz WAV for transcription
- Transcribes using whisper.cpp (configurable path, model, and args)
- Saves original uploads, transcript text, and rich JSON metadata
- Generates Markdown from transcripts using OpenAI-compatible LLMs
- Modern, responsive web UI for browsing, viewing, and managing transcriptions
- All configuration (paths, API keys, prompts, etc.) is read from `config.yaml`
- Robust error logging to `server.log`

## Requirements
- Python 3.8+
- FastAPI
- Uvicorn
- PyYAML
- python-multipart
- pydub
- openai (>=1.0.0)
- markdown2
- ffmpeg (system package, for audio/video conversion)

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure ffmpeg is installed:
   ```bash
   sudo apt install ffmpeg
   ```
3. Start the API server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --reload
   ```
4. (Optional) Start the web UI:
   ```bash
   uvicorn webui:app --reload --host 0.0.0.0 --port 8001
   ```
5. Upload audio/video files via POST to `/upload-audio`.
6. Browse/manage transcriptions at `http://localhost:8001/`.

## Configuration
Edit `config.yaml` to set all directories, whisper.cpp, and LLM settings. Example:

```yaml
upload_dir: "uploads"
transcriptions_dir: "transcriptions"
markdowns_dir: "markdowns"
server:
  host: "0.0.0.0"
  port: 8000
whisper:
  exe_path: "~/whisper.cpp/build/bin/whisper-cli"
  model_path: "~/whisper.cpp/models/ggml-small.bin"
  extra_args: "-l auto -nt"
llm:
  host: "https://api.openai.com"
  port: 443
  api_key: "sk-..."
  model: "gpt-4"
  prompt: "Polish this transcript into a clean, readable Markdown document:"
```

## Metadata
Each transcription JSON includes:
- datetime, source, original_filename, audio_length_sec, file_size, whisper_model, whisper_args, status, error, language, transcription_text, markdown_file, markdown_title

## Notes
- Only original uploads are archived; temp files are deleted after use.
- All file operations are robust to errors and race conditions.
- Never expose API keys or sensitive config in responses or logs.
- The web UI uses a modern, accessible design inspired by instagrapi docs.
