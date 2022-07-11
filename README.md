# SimilarString
Compute the score of similarity between two strings.

# Build
`docker build -t mlserver .`

# Run
Bind to Port 5000.
`docker run -p 5000:5000/tcp -itd --name mlserver mlserver`

# Logs
`docker logs mlserver` or `docker logs -f mlserver`

# Usage
`curl -X POST --data '{"s1":"this is a book", "s2":"that is a car"}' http://127.0.0.1:5000`
> {"score": 0.22442716360092163}
