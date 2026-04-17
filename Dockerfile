FROM python:3.10-slim

# Cài đặt TeXLive (Toán học) và pdf2svg
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-pictures \
    texlive-latex-extra \
    texlive-fonts-recommended \
    pdf2svg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy và cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY main.py .

# Mở cổng 8000 và chạy Uvicorn
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]