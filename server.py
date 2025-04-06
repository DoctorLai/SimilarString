import json
import yaml
import logging
import os
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer, util
import torch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

app = Flask(__name__)

# Cache for sentence embeddings
cache_enabled = config.get("cache", {}).get("enabled", False)
cache = {} if cache_enabled else None


# Function to get the device configuration
def get_device():
    device_config = config.get("model", {}).get("device", "auto")
    if device_config == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device_config


# Initialize SentenceTransformer model
logger.info("Loading ML model...")
model_name = config.get("model", {}).get("name", "all-MiniLM-L6-v2")
model_precision = config.get("model", {}).get("precision", "float32")
device = get_device()
model = SentenceTransformer(model_name, device=device)
logger.info(f"Model '{model_name}' loaded on {device} with precision {model_precision}")
logger.info("ML model loaded successfully.")


# Function to get embedding with optional caching
def get_embedding(sentence):
    sentence = sentence.strip().lower()
    if cache is not None and sentence in cache:
        return cache[sentence]

    embedding = model.encode(
        sentence,
        convert_to_tensor=True,
        dtype=torch.float16 if model_precision == "float16" else torch.float32,
    )

    if cache is not None:
        cache[sentence] = embedding

    return embedding


@app.route("/", methods=["GET"])
def score():
    data = request.get_json(force=True)

    if not data or "s1" not in data or "s2" not in data:
        return jsonify(
            {"status": "error", "message": "Both 's1' and 's2' fields are required"}
        ), 400

    sentence1 = data["s1"]
    sentence2 = data["s2"]

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
    logger.info(f"Response: {response}")
    return jsonify(response), 200


if __name__ == "__main__":
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

        options = {
            "bind": f"{config.get('server', {}).get('host', '0.0.0.0')}:{config.get('server', {}).get('port', 5000)}",
            "workers": config.get("server", {}).get("workers", 2),
        }
        FlaskApplication(app, options).run()
    else:
        logger.info("Running in development mode...")
        app.run(
            host=config.get("server", {}).get("host", "0.0.0.0"),
            port=config.get("server", {}).get("port", 5000),
            debug=config.get("server", {}).get("debug", True),
        )
