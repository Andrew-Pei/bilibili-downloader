FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY index.html bilibili_gui.py ./

RUN mkdir -p /app/downloads

EXPOSE 7860

ENV HOST=0.0.0.0
ENV PORT=7860

CMD ["python", "bilibili_gui.py"]
