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
        url = f"{self.base_url}/api/generate"
        prompt = (
            self.prompt +
            "\n\nReturn a JSON object with the following fields: markdown (the polished markdown text), title (a human-friendly title for the transcript), and file_name (a short, relevant file name for the markdown, suitable for Obsidian)." 
        )
        data = {
            "model": self.model,
            "prompt": f"{prompt}\n\n{transcript_text}",
            "stream": False
        }
        try:
            response = requests.post(url, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            return f"Error: {e}"
