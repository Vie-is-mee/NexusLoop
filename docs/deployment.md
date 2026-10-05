# Deployment notes

The MVP is a single FastAPI service that also serves the frontend, so deployment only needs one web process.

## Generic Python host

Build/install:

```bash
pip install -r requirements.txt
```

Start:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Docker host

```bash
docker build -t nexusloop .
docker run -p 8000:8000 nexusloop
```

## Demo-link checklist

Before sharing a public URL:

1. Open it in an incognito/private window.
2. Confirm the first case loads without any API key.
3. Run the hero path: legal PASS -> water-quality recommendation.
4. Open `Safety stop demo` and confirm the agent is blocked.
5. Check tablet/mobile layout once.
6. Reset the hero case before recording.
7. Do not add real company confidential data to the public deployment.
