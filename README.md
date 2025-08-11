# Web Transcriber FastAPI Server

This project is a modular FastAPI server for audio/video transcription and post-processing. It supports:
- Audio/video file upload via POST (supports .m4a, .mp4, and more)
- Audio conversion to 16-bit mono 16kHz WAV for transcription
- Transcription using whisper.cpp (configurable via config.yaml)
- Saving original uploads, JSON metadata, and transcript text
- Web UI for browsing, viewing, and managing transcriptions
- Markdown generation from transcripts using a local LLM (Ollama, OpenAI-compatible)
- All directories and API/configs are set in config.yaml

## Features
- Accepts audio/video uploads via POST (`/upload-audio`)
- Converts audio/video to 16-bit mono 16kHz WAV for transcription
- Transcribes using [whisper.cpp](https://github.com/ggml-org/whisper.cpp) (configurable path, model, and args)
- Saves original uploads, transcript text, and rich JSON metadata
- Generates Markdown from transcripts using a local LLM via [Ollama](https://ollama.com/) (configurable prompt/model)
- Modern, responsive web UI for browsing, viewing, and managing transcriptions
- All configuration (paths, API keys, prompts, etc.) is read from `config.yaml`
- Robust error logging to `server.log`
- Systemd service files for production deployment

## Requirements

### System Dependencies
- Python 3.8+
- ffmpeg (for audio/video conversion)
- whisper.cpp (for local transcription)
- [Ollama](https://ollama.com/) (for local LLM markdown generation)

### Python Dependencies
- FastAPI
- Uvicorn
- PyYAML
- python-multipart
- requests
- markdown2

## Installation

### 1. Install System Dependencies

#### Install ffmpeg
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

```

#### Install whisper.cpp
```bash
# See https://github.com/ggml-org/whisper.cpp

```

#### Install Ollama
```bash
# See https://ollama.com/download for your platform
```

### 2. Install Python Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure the Application
```bash
# Copy the example config and edit with your settings
cp config.yaml.example config.yaml
# Edit config.yaml and add your Ollama and whisper.cpp paths
```

## Usage

### Running the Server
1. Start the API server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --reload
   ```

2. Start the web UI:
   ```bash
   uvicorn webui:app --reload --host 0.0.0.0 --port 8001
   ```

3. (Production) Use the provided systemd service files:
   ```bash
   sudo cp webtranscriber-main.service /etc/systemd/system/
   sudo cp webtranscriber-webui.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now webtranscriber-main
   sudo systemctl enable --now webtranscriber-webui
   ```

4. Upload audio/video files via POST to `/upload-audio`.

5. Browse/manage transcriptions at `http://localhost:8001/`.

## Debian Package Installation

### 1. Install System Dependencies
- Python 3.8+
- ffmpeg (for audio/video conversion)
- whisper.cpp (for local transcription)
- [Ollama](https://ollama.com/) (for local LLM markdown generation)

### 2. Install the .deb Package
```bash
sudo dpkg -i web-transcriber_1.0.0.deb
```
- This will install all application files to `/opt/web-transcriber`.
- A dedicated system user `webtranscriber` will be created if it does not exist.
- A Python virtual environment will be created in `/opt/web-transcriber/.venv` and all dependencies installed automatically.
- Systemd services will be installed and started for both backend and frontend.

### 3. Services
- API backend: `webtranscriber-main` (serves FastAPI backend)
- Web UI: `webtranscriber-webui` (serves frontend web interface)

Check status:
```bash
systemctl status webtranscriber-main webtranscriber-webui
```

### 4. Configuration
- Edit `/opt/web-transcriber/config.yaml` to set all directories, whisper.cpp, and LLM settings.
- Example:

```yaml
backend_server:
  host: "0.0.0.0"
  port: 8000
frontend_server:
  host: "0.0.0.0"
  port: 8001
upload_dir: "uploads"
transcriptions_dir: "transcriptions"
markdowns_dir: "markdowns"
whisper:
  exe_path: "~/whisper.cpp/build/bin/whisper-cli"
  model_path: "~/whisper.cpp/models/ggml-small.bin"
  extra_args: "-l auto -nt"
ollama:
  host: "http://localhost"
  port: 11434
  model: "llama3"
  prompt: "Polish this transcript into a clean, readable Markdown document:"
```

### 5. Usage
- Upload audio/video files via POST to `/upload-audio`.
- Browse/manage transcriptions at `http://localhost:8001/`.

## Manual (Development) Installation

If you are not using the .deb package, you can install manually:

1. Install system dependencies (see above).
2. Clone the repo and create a venv:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Copy and edit `config.yaml.example` as needed.
4. Start the backend:
   ```bash
   python main.py --backend
   ```
5. Start the frontend:
   ```bash
   python main.py --frontend
   ```

## Metadata
Each transcription JSON includes:
- datetime, source, original_filename, audio_length_sec, file_size, whisper_model, whisper_args, status, error, language, transcription_text, markdown_file, markdown_title

## Notes
- All services run as the `webtranscriber` system user for security.
- All files and data are stored in `/opt/web-transcriber`.
- Only original uploads are archived; temp files are deleted after use.
- All file operations are robust to errors and race conditions.
- Never expose API keys or sensitive config in responses or logs.
- The web UI uses a modern, accessible design with orange-accented headers and improved readability.
- Markdown generation is fully automated after transcription completes.
- End-to-end tests and systemd service files are provided for production use.
