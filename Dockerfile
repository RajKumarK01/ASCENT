# Hosted Agent platform requires x86_64 (linux/amd64).
# Build: docker build --platform linux/amd64 -t ascent:v1 .
FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hosted Agent Responses protocol listens on 8088 by convention.
EXPOSE 8088

CMD ["python", "-m", "src.server"]
