# Use a lightweight Python 3.10 base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies including wget
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements.txt first (if it exists)
COPY requirements.txt /app/requirements.txt

# Install CPU-only PyTorch first (to avoid CUDA dependencies)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies with retry and timeout settings
RUN pip install --no-cache-dir --timeout=300 --retries=5 \
    sentence-transformers \
    psutil \
    py-cpuinfo \
    Pillow \
    scikit-learn \
    scipy \
    transformers \
    jinja2 \
    networkx \
    sympy

# Install ctransformers separately with more retries due to large size
RUN pip install --no-cache-dir --timeout=600 --retries=10 ctransformers

# Install remaining requirements without hash verification
RUN pip install --no-cache-dir --timeout=300 --retries=5 --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt || true

# Copy and run model download script
COPY download_models.sh /app/download_models.sh
RUN chmod +x /app/download_models.sh && /app/download_models.sh

# Copy the rest of the project files
COPY . /app

# Set entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]


# Default command (can be overridden)
CMD ["--base-dir", "/app/Challenge_1b", "--output-dir", "/app/output"]