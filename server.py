import json
from sentence_transformers import SentenceTransformer, util
import numpy as np
from flask import Flask, request

app = Flask(__name__)

print("Loading ML model...")
model = SentenceTransformer('stsb-roberta-large')
print("OK!")

sentence1 = "I like Python because I can build AI applications"
sentence2 = "I like Python because I can do data analytics"
# encode sentences to get their embeddings
embedding1 = model.encode(sentence1, convert_to_tensor=True)
embedding2 = model.encode(sentence2, convert_to_tensor=True)
# compute similarity scores of two embeddings
cosine_scores = util.pytorch_cos_sim(embedding1, embedding2)
print("Sentence 1:", sentence1)
print("Sentence 2:", sentence2)
print("Similarity score:", cosine_scores.item())

@app.route('/', methods=['POST']) 
def score():
    data = request.get_json(force=True)
    print(data)
    if "s1" not in data or "s2" not in data:
        return
    sentence1 = data['s1']
    sentence2 = data['s2']
    if not sentence1 or not sentence2:
        return
    if 'test' in data:
        score = data['test']
    else:    
        embedding1 = model.encode(sentence1, convert_to_tensor=True)
        embedding2 = model.encode(sentence2, convert_to_tensor=True) 
        cosine_scores = util.pytorch_cos_sim(embedding1, embedding2)   
        score = cosine_scores.item()
    data = json.dumps({
        "score": score
    })
    print(data)
    return data 

if __name__ == "__main__":
    print("Starting the server....")    
    app.run(host='0.0.0.0', port=5000)

