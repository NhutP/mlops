# Use slim Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# --- Install OpenMPI for mpirun ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    openmpi-bin openmpi-common libopenmpi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . .
# COPY train_xgboost.py .

# Install Python dependencies
RUN pip install --no-cache-dir \
    xgboost \
    numpy \
    pandas \
    scikit-learn \
    sqlalchemy \
    psycopg2-binary \
    feast \
    feast[postgres]

# Expose tracker port (default for Rabit)
EXPOSE 9091

# Entry point (can override in Kubernetes or CLI)
ENTRYPOINT ["python", "train_xgboost.py"]