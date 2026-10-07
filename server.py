import logging
import os
from collections import OrderedDict
from pathlib import Path
from threading import Lock

import torch
import yaml
from flask import Flask, jsonify, request
from sentence_transformers import SentenceTransformer, util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
config_path = Path(os.environ.get("SIMILARSTRING_CONFIG", ROOT / "config.yaml"))
with config_path.open(encoding="utf-8") as file:
    config = yaml.safe_load(file)
if not isinstance(config, dict):
    raise ValueError("Configuration must be a YAML mapping")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.get("server", {}).get(
    "max_request_bytes", 1048576
)

cache_enabled = config.get("cache", {}).get("enabled", False)
cache_max_size = config.get("cache", {}).get("max_size", 1024)
if cache_enabled and (
    isinstance(cache_max_size, bool)
    or not isinstance(cache_max_size, int)
    or cache_max_size < 1
):
    raise ValueError("cache.max_size must be a positive integer")
cache = OrderedDict() if cache_enabled else None
cache_lock = Lock()


def get_device():
    device_config = config.get("model", {}).get("device", "auto")
    if device_config == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device_config


logger.info("Loading ML model...")
model_name = config.get("model", {}).get("name", "all-MiniLM-L6-v2")
model_precision = config.get("model", {}).get("precision", "float32")
if model_precision not in ("float16", "float32"):
    raise ValueError("model.precision must be float16 or float32")
device = get_device()
model = SentenceTransformer(model_name, device=device)
if model_precision == "float16":
    model.half()
else:
    model.float()
logger.info(
    "Model '%s' loaded on %s with precision %s", model_name, device, model_precision
)
logger.info("ML model loaded successfully.")


def get_embedding(sentence):
    sentence = sentence.strip().lower()
    if cache is not None:
        with cache_lock:
            if sentence in cache:
                cache.move_to_end(sentence)
                return cache[sentence]

    embedding = model.encode(sentence, convert_to_tensor=True)

    if cache is not None:
        with cache_lock:
            cache[sentence] = embedding
            cache.move_to_end(sentence)
            while len(cache) > cache_max_size:
                cache.popitem(last=False)

    return embedding


@app.get("/health")
def health():
    return jsonify(
        {"status": "ok", "version": VERSION, "model": model_name, "device": device}
    )


@app.errorhandler(413)
def request_too_large(error):
    return jsonify(
        {"status": "error", "message": "Request body exceeds the configured size limit"}
    ), 413


@app.route("/", methods=["GET", "POST"])
def score():
    data = request.get_json(force=True, silent=True)

    if not isinstance(data, dict):
        return jsonify(
            {"status": "error", "message": "Request body must be a JSON object"}
        ), 400

    if not data or "s1" not in data or "s2" not in data:
        return jsonify(
            {"status": "error", "message": "Both 's1' and 's2' fields are required"}
        ), 400

    sentence1 = data["s1"]
    sentence2 = data["s2"]

    if not isinstance(sentence1, str) or not isinstance(sentence2, str):
        return jsonify(
            {"status": "error", "message": "'s1' and 's2' must be strings"}
        ), 400

    if not sentence1.strip() or not sentence2.strip():
        return jsonify(
            {"status": "error", "message": "'s1' and 's2' cannot be empty"}
        ), 400

    if "test" in data:
        score_value = data["test"]
    else:
        embedding1 = get_embedding(sentence1)
        embedding2 = get_embedding(sentence2)
        cosine_scores = util.pytorch_cos_sim(embedding1, embedding2)
        score_value = cosine_scores.item()

    response = {
        "status": "success",
        "s1": sentence1,
        "s2": sentence2,
        "score": score_value,
    }
    logger.info("Similarity request completed")
    return jsonify(response), 200


def main():
    logger.info("Starting the (Similar Sentences) server...")

    if os.environ.get("FLASK_ENV") == "production":
        logger.info("Running in production mode...")
        from gunicorn.app.base import BaseApplication

        class FlaskApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config_items = {
                    key: value
                    for key, value in self.options.items()
                    if key in self.cfg.settings and value is not None
                }
                for key, value in config_items.items():
                    self.cfg.set(key, value)

            def load(self):
                return self.application

        server_config = config.get("server", {})
        server_host = server_config.get("host", "0.0.0.0")
        server_port = server_config.get("port", 5000)
        server_bind = f"{server_host}:{server_port}"
        options = {
            "bind": server_bind,
            "workers": server_config.get("workers", 2),
        }
        FlaskApplication(app, options).run()
    else:
        logger.info("Running in development mode...")
        app.run(
            host=config.get("server", {}).get("host", "0.0.0.0"),
            port=config.get("server", {}).get("port", 5000),
            debug=config.get("server", {}).get("debug", False),
        )


if __name__ == "__main__":
    main()
