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
- Transcribes using [whisper.cpp](https://github.com/ggml-org/whisper.cpp) (configurable path, model, and args)
- Saves original uploads, transcript text, and rich JSON metadata
- Generates Markdown from transcripts using OpenAI-compatible LLMs
- Modern, responsive web UI for browsing, viewing, and managing transcriptions
- All configuration (paths, API keys, prompts, etc.) is read from `config.yaml`
- Robust error logging to `server.log`

## Requirements

### System Dependencies
- Python 3.8+
- ffmpeg (for audio/video conversion)
- whisper.cpp (for local transcription)

### Python Dependencies
- FastAPI
- Uvicorn
- PyYAML
- python-multipart
- pydub
- openai (>=1.0.0)
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

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Application
```bash
# Copy the example config and edit with your settings
cp config.yaml.example config.yaml
# Edit config.yaml and add your OpenAI API key and whisper.cpp paths
```

## Usage
## Usage

### Running the Server
1. Start the API server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --reload
   ```

2. (Optional) Start the web UI:
   ```bash
   uvicorn webui:app --reload --host 0.0.0.0 --port 8001
   ```

3. Upload audio/video files via POST to `/upload-audio`.

4. Browse/manage transcriptions at `http://localhost:8001/`.

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
