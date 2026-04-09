# Install the app and dependencies inside the image (nothing required on the host except Docker).
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["pocketsmith-mcp"]
