import json
import yaml
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer, util
import torch

# Load configuration from YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

app = Flask(__name__)

# Cache for sentence embeddings
cache = {} if config["cache"]["enabled"] else None

# Function to get the device configuration
def get_device():
    if config["model"]["device"] == 'auto':
        return 'cuda' if torch.cuda.is_available() else 'cpu'
    return config["model"]["device"]

# Initialize SentenceTransformer model based on YAML config
print("Loading ML model...")
model = SentenceTransformer(config["model"]["name"], device=get_device())
print("Model loaded on", get_device())

# Function to get embedding with optional caching
def get_embedding(sentence):
    if cache is not None and sentence in cache:
        return cache[sentence]
    
    embedding = model.encode(sentence, convert_to_tensor=True, 
                             dtype=torch.float16 if config["model"]["precision"] == 'float16' else torch.float32)
    
    if cache is not None:
        cache[sentence] = embedding
    return embedding

@app.route('/', methods=['POST'])
def score():
    data = request.get_json(force=True)
    
    # Check if both 's1' and 's2' are provided in the request
    if "s1" not in data or "s2" not in data:
        return jsonify({"error": "Both 's1' and 's2' fields are required"}), 400
    
    sentence1 = data['s1']
    sentence2 = data['s2']
    
    # Check if the sentences are not empty
    if not sentence1 or not sentence2:
        return jsonify({"error": "'s1' and 's2' cannot be empty"}), 400

    # If 'test' is in the data, use it directly, otherwise calculate the score
    if 'test' in data:
        score = data['test']
    else:
        embedding1 = get_embedding(sentence1)
        embedding2 = get_embedding(sentence2)
        cosine_scores = util.pytorch_cos_sim(embedding1, embedding2)
        score = cosine_scores.item()
    
    response = {
        "score": score
    }
    print(response)
    return jsonify(response), 200

if __name__ == "__main__":
    print("Starting the server....")
    
    # Run Flask with Gunicorn if in production mode (optional)
    import os
    if os.environ.get("FLASK_ENV") == "production":
        from gunicorn.app.base import BaseApplication
        
        class FlaskApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key, value)

            def load(self):
                return self.application

        options = {
            'bind': f"{config['server']['host']}:{config['server']['port']}",
            'workers': config['server']['workers']
        }
        FlaskApplication(app, options).run()
    else:
        app.run(host=config['server']['host'], port=config['server']['port'])

