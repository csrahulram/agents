"""Minimal Ollama client (stdlib only)."""
import json
import urllib.request


class LLM:
    def __init__(self, host, model, temperature=0.3, num_ctx=8192, keep_alive="30m"):
        self.host = host.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.keep_alive = keep_alive

    def _post(self, path, payload, timeout=600):
        req = urllib.request.Request(
            self.host + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())

    def chat(self, messages, json_mode=False):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {"temperature": self.temperature, "num_ctx": self.num_ctx},
        }
        if json_mode:
            payload["format"] = "json"
        return self._post("/api/chat", payload)["message"]["content"]

    def chat_json(self, messages, retries=2):
        """Ask for JSON; retry with the parse error if the small model slips."""
        last = ""
        for _ in range(retries + 1):
            last = self.chat(messages, json_mode=True)
            try:
                return json.loads(last)
            except json.JSONDecodeError as e:
                messages = messages + [
                    {"role": "assistant", "content": last},
                    {"role": "user", "content": f"Invalid JSON ({e}). Reply with valid JSON only."},
                ]
        raise ValueError(f"{self.model} did not return JSON: {last[:300]}")

    def embed(self, text):
        return self._post("/api/embed", {"model": self.model, "input": text[:8000]})["embeddings"][0]


def list_local_models(host):
    with urllib.request.urlopen(host.rstrip("/") + "/api/tags", timeout=10) as r:
        return {m["name"] for m in json.loads(r.read())["models"]}
