from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
import json
from datetime import datetime
import urllib.parse
import requests
import markdown2
from ollama_client import OllamaClient

TRANSCRIPTIONS_DIR = "transcriptions"
ARCHIVE_DIR = os.path.join(TRANSCRIPTIONS_DIR, "archive")
MARKDOWNS_DIR = "markdowns"

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

os.makedirs(MARKDOWNS_DIR, exist_ok=True)

# LLM config loader (kept for legacy, but not used for Ollama)
def get_llm_config():
    import yaml
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    llm_cfg = config.get("llm", {})
    return {
        "host": llm_cfg.get("host", "https://api.openai.com"),
        "port": llm_cfg.get("port", 443),
        "api_key": llm_cfg.get("api_key", ""),
        "model": llm_cfg.get("model", "gpt-4"),
        "prompt": llm_cfg.get("prompt", "Polish this transcript into a clean, readable Markdown document:")
    }

def call_llm(transcript_text: str) -> dict:
    # Use Ollama for local LLM inference
    client = OllamaClient()
    response = client.generate_markdown(transcript_text)
    # Debug: log the raw response from OllamaClient
    try:
        with open("server.log", "a") as logf:
            logf.write(f"[CALL_LLM RAW RESPONSE]: {repr(response)}\n")
    except Exception:
        pass
    import json as _json
    # If response is a dict, return as is
    if isinstance(response, dict):
        return response
    # If response is a string, try to parse as JSON
    try:
        resp_str = response.strip()
        if resp_str.startswith('```json'):
            resp_str = resp_str.split('```json')[1].split('```')[0].strip()
        elif resp_str.startswith('```'):
            resp_str = resp_str.split('```')[1].split('```')[0].strip()
        return _json.loads(resp_str)
    except Exception:
        return {"markdown": response, "title": "", "file_name": ""}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    files = [f for f in os.listdir(TRANSCRIPTIONS_DIR) if f.endswith(".json") and os.path.isfile(os.path.join(TRANSCRIPTIONS_DIR, f))]
    files.sort(reverse=True)
    # Build left panel: list of files
    file_links = []
    for fname in files:
        with open(os.path.join(TRANSCRIPTIONS_DIR, fname), "r") as jf:
            meta = json.load(jf)
        dt = meta.get("datetime", "")
        orig = meta.get("original_filename", "")
        md_title = meta.get("markdown_title", "")
        # Format datetime to human-friendly string
        try:
            dt_obj = datetime.fromisoformat(dt.replace("Z", ""))
            dt_str = dt_obj.strftime("%b %d, %Y %H:%M")
        except Exception:
            dt_str = dt
        # Show file name, then markdown title (if any), then date/time
        file_links.append(f"<li><a href='/?file={fname}'>{orig}{'<br><span style=\"color:var(--accent);font-weight:bold;\">'+md_title+'</span>' if md_title else ''}<br><small>{dt_str}</small></a></li>")
    # Parse query param
    url = str(request.url)
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    fname = params.get('file', [None])[0]
    def render_right_panel(fname):
        if not fname:
            return "<div><em>Select a transcription to view details.</em></div>"
        path = os.path.join(TRANSCRIPTIONS_DIR, fname)
        if not os.path.exists(path):
            return "<div><em>File not found.</em></div>"
        with open(path, "r") as jf:
            meta = json.load(jf)
        text = meta.get("transcription_text", "")
        md_name = meta.get("markdown_file")
        md_title = meta.get("markdown_title", "")
        md_html = ""
        if md_name:
            md_path = os.path.join(MARKDOWNS_DIR, md_name)
            if os.path.exists(md_path):
                with open(md_path, "r") as mf:
                    md_content = mf.read()
                md_html = f"<div style='margin-bottom:2em;'><h3>Markdown</h3><div class='md-rendered' style='background:#23272b;color:#f5f5f5;padding:1em;border-radius:8px;overflow-x:auto;'>{markdown2.markdown(md_content)}</div><a href='/download_md/{md_name}'>Download MD</a></div>"
        btns = f"""
        <a href='/download/{fname}'>Download JSON</a> |
        <a href='/generate_md/{fname}'>Generate MD</a> |
        <a href='/delete/{fname}'>Delete</a>
        """
        html = f"""
        <div>
        {md_html}
        <h2>{meta.get('original_filename','')}</h2>
        {'<h4 style="color:var(--accent);margin-top:0;">'+md_title+'</h4>' if md_title else ''}
        <pre style='white-space: pre-wrap;'>{text}</pre>
        {btns}
        </div>
        """
        return html
    html = f"""
    <html><head><title>Transcriptions</title>
    <link rel="stylesheet" href="/static/instagrapi.css">
    <style>
    body {{ display: flex; font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }}
    #left {{ width: 300px; min-width: 200px; padding: 1em; height: 100vh; overflow-y: auto; }}
    #right {{ flex: 1; padding: 2em; }}
    ul {{ list-style: none; padding: 0; }}
    .md-rendered {{ font-family: 'DejaVu Sans Mono', 'Consolas', 'Menlo', 'Monaco', monospace; }}
    .md-rendered h1, .md-rendered h2, .md-rendered h3, .md-rendered h4, .md-rendered h5, .md-rendered h6 {{ color: var(--accent); }}
    .md-rendered pre, .md-rendered code {{ background: #181c20; color: #00bcd4; border-radius: 4px; padding: 0.2em 0.4em; }}
    .md-rendered a {{ color: var(--accent); }}
    </style>
    </head><body>
    <div id='left'>
      <h2>Transcriptions</h2>
      <ul>
        {''.join(file_links)}
      </ul>
    </div>
    <div id='right'>
      {render_right_panel(fname)}
    </div>
    <script>
      document.querySelectorAll('#left a').forEach(function(a) {{
        a.onclick = function(e) {{
          e.preventDefault();
          window.location = this.href;
        }}
      }});
    </script>
    </body></html>
    """
    return HTMLResponse(content=html)

@app.get("/view/{fname}", response_class=HTMLResponse)
def view_transcription(fname: str):
    path = os.path.join(TRANSCRIPTIONS_DIR, fname)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    with open(path, "r") as jf:
        meta = json.load(jf)
    text = meta.get("transcription_text", "")
    html = f"""
    <html><head><title>View Transcription</title></head><body>
    <h2>Transcription: {fname}</h2>
    <pre>{text}</pre>
    <a href='/'>Back</a>
    </body></html>
    """
    return HTMLResponse(content=html)

@app.get("/download/{fname}")
def download_json(fname: str):
    path = os.path.join(TRANSCRIPTIONS_DIR, fname)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    return FileResponse(path, media_type="application/json", filename=fname)

@app.get("/delete/{fname}")
def delete_transcription(fname: str):
    path = os.path.join(TRANSCRIPTIONS_DIR, fname)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    os.remove(path)
    # Optionally remove .txt with same base name
    txt_path = os.path.splitext(path)[0] + ".txt"
    if os.path.exists(txt_path):
        os.remove(txt_path)
    return RedirectResponse(url="/", status_code=303)

@app.get("/generate_md/{fname}")
def generate_markdown(fname: str):
    path = os.path.join(TRANSCRIPTIONS_DIR, fname)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    with open(path, "r") as jf:
        meta = json.load(jf)
    transcript_text = meta.get("transcription_text", "")
    if not transcript_text:
        return HTMLResponse("<b>No transcript text found.</b>")
    llm_result = call_llm(transcript_text)
    # Log the raw LLM result for debugging
    try:
        with open("server.log", "a") as logf:
            logf.write(f"[LLM RESPONSE] {fname}: {repr(llm_result)}\n")
    except Exception:
        pass
    # If LLM returns an empty dict, show error and log warning
    if isinstance(llm_result, dict) and not llm_result:
        try:
            with open("server.log", "a") as logf:
                logf.write(f"[LLM WARNING] {fname}: LLM returned empty dict.\n")
        except Exception:
            pass
        return HTMLResponse(f"<b>Error: LLM returned an empty response. Check your Ollama model and prompt configuration.</b> <a href='/?file={fname}'>Back</a>")
    md_content = llm_result.get("markdown", "")
    md_title = llm_result.get("title", "")
    md_file_name = llm_result.get("file_name") or (os.path.splitext(fname)[0] + ".md")
    # Fallback: if markdown is empty, use the raw response as markdown
    if not md_content or not md_content.strip():
        if isinstance(llm_result, dict):
            for v in llm_result.values():
                if isinstance(v, str) and v.strip():
                    md_content = v
                    break
        if not md_content or not md_content.strip():
            md_content = str(llm_result)
    md_path = os.path.join(MARKDOWNS_DIR, md_file_name)
    with open(md_path, "w") as mf:
        mf.write(md_content)
    # Update JSON to link to markdown file and title
    meta["markdown_file"] = md_file_name
    if md_title:
        meta["markdown_title"] = md_title
    with open(path, "w") as jf:
        json.dump(meta, jf, ensure_ascii=False, indent=2)
    # Show warning if markdown is still empty
    if not md_content.strip():
        return HTMLResponse(f"<b>Warning: Markdown is empty. Check server.log for LLM response.</b> <a href='/download_md/{md_file_name}'>Download MD</a> | <a href='/?file={fname}'>Back</a>")
    return HTMLResponse(f"<b>Markdown generated and saved as {md_file_name}.</b> <a href='/download_md/{md_file_name}'>Download MD</a> | <a href='/?file={fname}'>Back</a>")

@app.get("/download_md/{md_name}")
def download_md(md_name: str):
    md_path = os.path.join(MARKDOWNS_DIR, md_name)
    if not os.path.exists(md_path):
        raise HTTPException(404, "Not found")
    return FileResponse(md_path, media_type="text/markdown", filename=md_name)
