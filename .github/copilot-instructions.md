<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://aka.ms/vscode-instructions-docs -->

# Project Overview
This is a modular FastAPI server for audio/video transcription and post-processing. The architecture is designed for extensibility, robust error handling, and clean separation of concerns:
- **API server** (`main.py`): Handles uploads, audio conversion, and transcription orchestration.
- **Web UI** (`webui.py`): Modern, responsive interface for browsing, viewing, and managing transcriptions and markdowns.
- **Config** (`config.yaml`): All paths, API keys, prompts, and model settings are loaded from here—never hardcode these in code.
- **Transcription**: Uses `whisper.cpp` via subprocess, with all parameters and model paths set in config.
- **LLM Markdown Generation**: Uses the official OpenAI Python SDK (>=1.0.0) for markdown generation, with prompt/model/config in `config.yaml`.
- **Storage**: Original uploads are archived; temp/intermediate files (e.g., .wav) are deleted after use. Metadata and transcripts are saved as JSON in `transcriptions_dir`, markdowns in `markdowns_dir`.

# Key Patterns & Conventions
- **All configuration** (paths, secrets, prompts, etc.) must be read from `config.yaml`.
- **Audio conversion** is modular (see `convert_audio` in `main.py`), easily extensible for new formats.
- **Transcription** is always run in a FastAPI background task; API returns immediately with status `processing` and a transcription ID.
- **Metadata** for each transcription is rich and always saved as JSON (see `meta` in `main.py`).
- **Web UI** uses a two-panel layout, with the left panel listing files and markdown titles, and the right panel showing details and management actions.
- **Markdown generation**: LLM is prompted to return a JSON with `markdown`, `title`, and `file_name`. These are linked in the transcription JSON for robust cross-referencing.
- **Logging**: All subprocess and error events are logged to `server.log`.
- **Security**: Never expose API keys or sensitive config in responses or logs.
- **UI Styling**: Uses a color palette and style inspired by [instagrapi docs](https://subzeroid.github.io/instagrapi/), see `/static/instagrapi.css`.

# Developer Workflows
- **Install dependencies**: `pip install -r requirements.txt` (requires `ffmpeg` system package)
- **Run API server**: `uvicorn main:app --host 0.0.0.0 --reload`
- **Run Web UI**: `uvicorn webui:app --host 0.0.0.0 --port 8001 --reload`
- **Upload**: POST to `/upload-audio` (see `main.py` for accepted formats)
- **Monitor**: Check `transcriptions/` for JSON status, or use the web UI for live updates

# Integration Points
- **whisper.cpp**: Called via subprocess, all args from config
- **OpenAI LLM**: Uses OpenAI SDK, all settings from config
- **Audio/Video**: Uses `pydub` for conversion and duration extraction

# Examples
- See `main.py` for the full upload/transcription/metadata flow
- See `webui.py` for UI logic, markdown rendering, and file management
- See `config.yaml` for a complete example of all required settings

# When in doubt
- Always use config.yaml for any configuration or secret
- Keep logic modular and extensible
- Ask for clarification if config structure or requirements are unclear
