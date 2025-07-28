#!/bin/bash
set -e

# Define model directory relative to the script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$SCRIPT_DIR/models"
mkdir -p "$MODEL_DIR"

# Download SentenceTransformer model
echo "Downloading SentenceTransformer model..."
pip install huggingface_hub
python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='sentence-transformers/all-MiniLM-L6-v2', local_dir='$MODEL_DIR/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf')"
if [ $? -ne 0 ]; then
    echo "Error: Failed to download SentenceTransformer model"
    exit 1
fi

# Download TinyLLaMA model
echo "Downloading TinyLLaMA model..."
TINYLLAMA_URL="https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
TINYLLAMA_PATH="$MODEL_DIR/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
wget -O "$TINYLLAMA_PATH" "$TINYLLAMA_URL"
if [ $? -ne 0 ] || [ ! -s "$TINYLLAMA_PATH" ]; then
    echo "Error: Failed to download TinyLLaMA model or file is empty"
    exit 1
fi

echo "Model download completed successfully!"