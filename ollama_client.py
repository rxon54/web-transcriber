import requests
import yaml

class OllamaClient:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        ollama_cfg = config.get("ollama", {})
        self.host = ollama_cfg.get("host", "http://localhost")
        self.port = ollama_cfg.get("port", 11434)
        self.model = ollama_cfg.get("model", "llama3")
        self.prompt = ollama_cfg.get("prompt", "Polish this transcript into a clean, readable Markdown document:")
        self.base_url = f"{self.host}:{self.port}"

    def generate_markdown(self, transcript_text):
        url = f"{self.base_url}/api/chat"
        prompt = (
            self.prompt +
            "\n\nReturn a JSON object with the following fields: markdown (the polished markdown text), title (a human-friendly title for the transcript), and file_name (a short, relevant file name for the markdown, suitable for Obsidian)." 
        )
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": f"{prompt}\n\n{transcript_text}"}
            ],
            "stream": False,
            "format": {
                "type": "object",
                "properties": {
                    "markdown": {"type": "string"},
                    "title": {"type": "string"},
                    "file_name": {"type": "string"}
                },
                "required": ["markdown", "title", "file_name"]
            },
            "options": {
                "temperature": 0
            }
        }
        # Log the full request payload
        try:
            with open("server.log", "a") as logf:
                logf.write(f"[OLLAMA REQUEST] {url}: {data}\n")
        except Exception:
            pass
        try:
            response = requests.post(url, json=data, timeout=120)
            # Log the raw HTTP response text
            try:
                with open("server.log", "a") as logf:
                    logf.write(f"[OLLAMA RAW RESPONSE] {response.text}\n")
            except Exception:
                pass
            response.raise_for_status()
            result = response.json()
            # For /api/chat endpoint, structured output is in message.content
            if 'message' in result and 'content' in result['message']:
                return result['message']['content']
            else:
                return result.get("response", "")
        except Exception as e:
            # Log the exception
            try:
                with open("server.log", "a") as logf:
                    logf.write(f"[OLLAMA ERROR] {e}\n")
            except Exception:
                pass
            return f"Error: {e}"
