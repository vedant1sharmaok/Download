FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -U yt-dlp

EXPOSE 8000
CMD ["python", "main.py"]
