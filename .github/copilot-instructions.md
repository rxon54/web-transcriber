<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://aka.ms/vscode-instructions-docs -->

# Copilot Instructions for web-transcriber

## Architecture Overview

- **API Server (`main.py`)**: Handles audio/video uploads, modular audio conversion (via `pydub`), and transcription orchestration using `whisper.cpp` (all subprocess args from `config.yaml`). Transcription runs in a FastAPI background task; API responds immediately with `processing` status and a transcription ID.
- **Web UI (`webui.py`)**: Modern, two-panel interface for browsing, viewing, and managing transcriptions and markdowns. Uses `/static/instagrapi.css` for styling.
- **Config (`config.yaml`)**: All paths, API keys, prompts, and model settings are loaded from here—never hardcode these in code.
- **Storage**: 
  - Original uploads are archived in `uploads/`.
  - Temp/intermediate files (e.g., `.wav`) are deleted after use.
  - Metadata and transcripts are saved as JSON in `transcriptions/`.
  - Markdown files are saved in `markdowns/`.

## Key Patterns & Conventions

- **All configuration** (paths, secrets, prompts, etc.) must be read from `config.yaml`.
- **Audio conversion** is modular (see `convert_audio` in `main.py`), easily extensible for new formats.
- **Transcription**: Always run as a FastAPI background task; metadata is rich and always saved as JSON.
- **Markdown generation**: Uses OpenAI SDK (>=1.0.0), with prompt/model/config in `config.yaml`. LLM is prompted to return a JSON with `markdown`, `title`, and `file_name`. These are linked in the transcription JSON for robust cross-referencing.
- **Web UI**: Left panel lists files and markdown titles; right panel shows details and management actions.
- **Logging**: All subprocess and error events are logged to `server.log`.
- **Security**: Never expose API keys or sensitive config in responses or logs.

## Developer Workflows

- **Install dependencies**: `pip install -r requirements.txt` (requires `ffmpeg` system package)
- **Run API server**: `uvicorn main:app --host 0.0.0.0 --reload`
- **Run Web UI**: `uvicorn webui:app --host 0.0.0.0 --port 8001 --reload`
- **Upload**: POST to `/upload-audio` (see `main.py` for accepted formats)
- **Monitor**: Check `transcriptions/` for JSON status, or use the web UI for live updates
- **Always update `project_tasks.txt` to reflect implementation progress and new requirements.**

## Integration Points

- **whisper.cpp**: Called via subprocess, all args from config
- **OpenAI LLM**: Uses OpenAI SDK, all settings from config
- **Audio/Video**: Uses `pydub` for conversion and duration extraction

## Examples

- See `main.py` for the full upload/transcription/metadata flow
- See `webui.py` for UI logic, markdown rendering, and file management
- See `config.yaml` for a complete example of all required settings

## When in doubt

- Always use `config.yaml` for any configuration or secret
- Keep logic modular and extensible
- Ask for clarification if config structure or requirements are unclear
- Always update `project_tasks.txt` to reflect implementation progress and new requirements.
