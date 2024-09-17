# String Similarity Server
A Simple Server to Compute the score of similarity between two strings.

# Build
`docker build -t mlserver .`

# Run
Bind to Port 5000.
`docker run -p 5000:5000 -itd --name mlserver mlserver`

# Logs
`docker logs mlserver` or `docker logs -f mlserver`

# Usage
`curl -X POST --data '{"s1":"this is a book", "s2":"that is a car"}' http://127.0.0.1:5000`
> {"score": 0.22442716360092163}

You can also run [./build-and-run.sh](./build-and-run.sh) to build the Docker image and run the server.

# Support
If you find this useful, consider buy me a cup of coffee, thanks! https://www.buymeacoffee.com/y0BtG5R
