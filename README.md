# SimilarString
Compute the score of similarity between two strings.

# Build
`docker build -t mlserver .`

# Run
`docker run -itd --name mlserver mlserver`

# Logs
`docker logs mlserver` or `docker logs -f mlserver`

# Port
5000

# Usage
`curl -x POST --data '{"s1":"this is a book", "s2":"that is a car"}' http://127.0.0.1:5000`
