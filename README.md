# Flask App with Sentence Transformers
[![Similarity Sentence API CI](https://github.com/DoctorLai/SimilarString/actions/workflows/ci.yaml/badge.svg)](https://github.com/DoctorLai/SimilarString/actions/workflows/ci.yaml)

This repository contains a Flask application that uses the SentenceTransformer model to compute the similarity between two input sentences. The application is containerized using Docker and is configured to run in both development and production environments using gunicorn.

A Simple Server to Compute the score of similarity between two strings.

## Features
- Flask Backend: A simple API built with Flask that accepts two sentences and returns their cosine similarity score.
- Sentence Transformers: Uses the SentenceTransformer model to encode sentences and compute their similarity.
- YAML Configurations: Reads settings such as model name, device configuration, and server options from a YAML file (config.yaml).
- Gunicorn: In production, the app is served using gunicorn for improved performance.

## Prerequisites
### Docker
- Python 3.x (if you want to run it locally without Docker)
- docker-compose (optional, if you want to use it to manage services)

## Getting Started
1. Clone the Repository
2. Modify the [config.yaml](./config.yaml)
3. Build and Run the Docker Container
Build the Docker image and run the container:
```bash
docker build -t mlserver .
docker run -p 5000:5000 mlserver
```
By default, the application runs in production mode with gunicorn.
4. Running in Development Mode
If you want to run the app in development mode with Flask’s built-in server and auto-reload, override the FLASK_ENV environment variable:
```bash
docker run -p 5000:5000 -e FLASK_ENV=development mlserver
```
5. Accessing the API
Once the Docker container is running, you can send a POST request to the server to compute the sentence similarity.

Example curl command:
```bash
curl -v -H "Content-type: application/json" --data '{"s1":"This is a Surface Studio Laptop","s2":"That is a car"}' http://127.0.0.1:5000
```
The response will contain the cosine similarity score between the two sentences.

6. Show the Logs
```bash
`docker logs mlserver` or `docker logs -f mlserver`
```

7. Docke scripts
A few handy shell scripts:
- [build.sh](./build.sh): builds the docker container.
- [stop.sh](./stop.sh): stops the docker container.
- [run.sh](./run.sh): runs the ML server.
- [restart.sh](./restart.sh): restarts the ML server aka [stop.sh](./stop.sh) and then [run.sh](./run.sh).
- [build-and-run.sh]: is the combination of [build.sh](./build.sh) and [restart.sh](./restart.sh).

Make sure you source [setup-env](./setup-env.sh) to set the variables first.

## Development (Without Docker)
To run the application locally without Docker:

1. Install Dependencies
First, ensure you have Python 3.x installed, then install the necessary Python packages:

```bash
pip install -r requirements.txt
```

2. Start the Flask Application
Start the app using the following command:

```bash
FLASK_ENV=development flask run
```

The server will be available at http://127.0.0.1:5000.

## Docker Compose (Optional)
To use docker-compose to manage services, you can create a docker-compose.yml file and run the application with:

```bash
docker-compose up --build -d
```

This will build and start the Flask application along with any additional services you define.

To view the logs using docker-compose, run:

```bash
docker-compose logs -f
```

To restart the docker-compose container, run:

```bash
docker-compose down  # Stop the containers
docker-compose up -d  # Start the containers in detached mode
```

Or simply:

```
docker-compose restart <service_name>
```

## Configuration
The application reads the following configurations from config.yaml:

- Model Settings: Specify the model name (e.g., paraphrase-MiniLM-L6-v2), device (auto, cuda, or cpu), and precision (float32 or float16).
- Caching: Enable or disable caching for sentence embeddings.
- Server Settings: Configure the host, port, and number of gunicorn workers.

## Production
In production, the app is served using gunicorn. You can customize the number of workers by modifying the [config.yaml](./config.yaml) file.

## Exposed Ports
The application exposes port 5000 by default. This can be modified in the docker run command or the config.yaml file.

## Tests
Use the following script to perform a basic integration test — it builds the Docker image, starts the server locally, sends a request, and verifies that the response has a 'status' of 'OK' with a status code of 200. In particular, there are two tests:

[integration-tests-docker.sh](./tests/integration-tests-docker.sh) tests the Docker image and [integration-tests-docker-compose.sh](./tests/integration-tests-docker-compose.sh) tests the [docker-compose.yml](./docker-compose.yml).

```bash
source ./setup-env.sh

## on success, exit code is 0.
## on failure, exit code is 1.
## test basic docker setup
./tests/integration-tests-docker.sh

## on success, exit code is 0.
## test docker compose
## on failure, exit code is 1.
./tests/integration-tests-docker-compose.sh

```

## License
This project is licensed under the [MIT License](./LICENSE).

## Contributing?
Contribution are absolutely welcome! Please follow the guidance [here](./CONTRIBUTING.md)

## Support me
If you like this and want to support me in continuous development, you can do the following:
- [Buy me a coffee](https://justyy.com/out/bmc)
- [Sponsor me](https://github.com/sponsors/DoctorLai)
- [Vote me as a witness](https://steemyy.com/witness-voting/?witness=justyy&action=approve)
- [Set me a Witness Proxy if you are too lazy to vote](https://steemyy.com/witness-voting/?witness=justyy&action=proxy)

<a rel="nofollow" href="http://steemyy.com/out/buymecoffee" target="_blank"><img src="https://user-images.githubusercontent.com/1764434/161362754-c45a85d3-5c80-4e10-b05c-62af49291d0b.png" alt="Buy me a Coffee"/></a>
