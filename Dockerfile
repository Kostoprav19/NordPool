FROM python:3.12-slim

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY main.py .
COPY config.yaml .

# Run the application
CMD ["python", "main.py"]