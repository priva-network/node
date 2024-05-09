# Priva Node

Running a Priva Node allows you to provide compute to Priva Network and earn for it.

Setup instructions can be found at [priva.gitbook.io/priva/compute-providers/run-a-compute-node](https://priva.gitbook.io/priva/compute-providers/run-a-compute-node)

# Development

To run in development node, set `PRIVA_ENV=DEV`.

```bash
PRIVA_ENV=DEV python main.py <cmd>
```

# Running as Docker Image

Build the Docker image:

```
docker build -t priva-node .
```

Run the image in interactive mode using port 8000:

```
docker run -it -p 8000:8000 -v /var/run/docker.sock:/var/run/docker.sock priva-node
```

Start the IPFS daemon as a background process:

```
ipfs daemon &
```
