#!/usr/bin/env python3
"""
Chavruta — local Whisper transcription backend.

Why this exists
---------------
The browser's built-in Web Speech API is weak for Hebrew and effectively
unusable for the Aramaic that a rabbi mixes into a shiur. This server runs
OpenAI Whisper *locally* (via faster-whisper / CTranslate2) so audio never
leaves the machine and Hebrew + Aramaic are transcribed by a real model.

It does two jobs:
  1. Serves the static app (index.html) — same origin, so no CORS pain.
  2. POST /transcribe  — accepts a short audio blob (webm/ogg/wav) and returns
     {"text": "..."} transcribed in Hebrew (Aramaic is written in the same
     script, so language='he' captures it).

Run it
------
    cd gemara-app
    ./.venv/bin/python server.py
    # then open http://localhost:8097

Choose a model (accuracy vs. speed) with the WHISPER_MODEL env var:
    WHISPER_MODEL=small      ./.venv/bin/python server.py   # fastest
    WHISPER_MODEL=medium     ./.venv/bin/python server.py   # default, balanced
    WHISPER_MODEL=large-v3   ./.venv/bin/python server.py   # best, slower on CPU
    WHISPER_MODEL=ivrit-ai/faster-whisper-v2-d4 ...         # Hebrew-tuned
The model downloads once (cached in ~/.cache/huggingface) then runs offline.
"""

import io
import json
import os
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8097"))
MODEL_NAME = os.environ.get("WHISPER_MODEL", "medium")
# int8 keeps CPU inference fast with minimal accuracy loss.
COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE", "int8")
LANGUAGE = os.environ.get("WHISPER_LANG", "he")

# ── Lazy, thread-safe model singleton ─────────────────────────────────────
_model = None
_model_lock = threading.Lock()


def get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from faster_whisper import WhisperModel
                print(f"[whisper] loading model '{MODEL_NAME}' "
                      f"(compute={COMPUTE_TYPE})…", flush=True)
                _model = WhisperModel(MODEL_NAME, device="cpu",
                                      compute_type=COMPUTE_TYPE)
                print("[whisper] model ready.", flush=True)
    return _model


def transcribe_bytes(audio_bytes: bytes) -> str:
    """Decode an audio blob and return Hebrew/Aramaic text."""
    model = get_model()
    # faster-whisper decodes via bundled PyAV, so it reads webm/ogg/wav
    # straight from a temp file — no system ffmpeg required.
    suffix = ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        segments, _info = model.transcribe(
            tmp_path,
            language=LANGUAGE,
            task="transcribe",
            vad_filter=True,                       # skip silence
            vad_parameters=dict(min_silence_duration_ms=300),
            beam_size=5,
            condition_on_previous_text=False,      # each chunk independent
            initial_prompt="שיעור גמרא בעברית ובארמית.",  # bias toward the domain
        )
        return "".join(s.text for s in segments).strip()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ── HTTP handler ──────────────────────────────────────────────────────────
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def log_message(self, fmt, *args):
        # Keep the console quiet except for our own prints.
        pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_json({"ok": True, "model": MODEL_NAME})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/transcribe":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            audio = self.rfile.read(length) if length else b""
            if not audio:
                self._send_json({"text": ""})
                return
            text = transcribe_bytes(audio)
            self._send_json({"text": text})
        except Exception as exc:  # noqa: BLE001 — report any failure to the client
            sys.stderr.write(f"[transcribe error] {exc}\n")
            self._send_json({"error": str(exc)}, 500)


def main():
    # Warm the model on startup so the first utterance isn't slow.
    threading.Thread(target=get_model, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[server] Chavruta running →  http://localhost:{PORT}", flush=True)
    print(f"[server] transcription model: {MODEL_NAME}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] shutting down.", flush=True)
        server.shutdown()


if __name__ == "__main__":
    main()
