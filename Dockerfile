FROM python:3.11-slim

# Avoid writing .pyc files and enable unbuffered output for real-time logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root sandbox user for security with home directory
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

ENV HOME=/home/appuser
ENV PYTHONPATH=/app
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY app/ ./app
COPY .env* ./

# Assign ownership to non-root sandbox user
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

HEALTHCHECK CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
