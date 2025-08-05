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

# macOS
brew install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

#### Install whisper.cpp
```bash
# Clone and build whisper.cpp
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
make

# Download a model (e.g., small model)
bash ./models/download-ggml-model.sh small
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
ollama:
  host: "http://localhost"
  port: 11434
  model: "llama3"
  prompt: "Polish this transcript into a clean, readable Markdown document:"
```

## Metadata
Each transcription JSON includes:
- datetime, source, original_filename, audio_length_sec, file_size, whisper_model, whisper_args, status, error, language, transcription_text, markdown_file, markdown_title

## Notes
- Only original uploads are archived; temp files are deleted after use.
- All file operations are robust to errors and race conditions.
- Never expose API keys or sensitive config in responses or logs.
- The web UI uses a modern, accessible design with orange-accented headers and improved readability.
- Markdown generation is fully automated after transcription completes.
- End-to-end tests and systemd service files are provided for production use.
