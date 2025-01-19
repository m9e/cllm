#!/bin/bash

# Ensure pipx is installed and configured
python -m pip install --upgrade pip pipx
pipx ensurepath

# Clean up old installation
sudo rm -f /usr/local/bin/cllm

# Install with pipx from the correct directory
cd "$(dirname "$0")"  # Move to the script's directory
pipx install . --force

# Reload PATH
export PATH="$HOME/.local/bin:$PATH"

# Set up Azure OpenAI credentials using existing environment variables if present
echo "Setting up Azure OpenAI credentials..."
if [ -n "$AZURE_OPENAI_API_KEY" ]; then
    echo "AZURE_OPENAI_API_KEY is set"
else
    echo "Warning: AZURE_OPENAI_API_KEY environment variable not found"
    echo "Please set it up with: export AZURE_OPENAI_API_KEY=your_api_key_here"
fi

if [ -n "$AZURE_OPENAI_ENDPOINT" ]; then
    echo "export AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT"
else
    echo "Warning: AZURE_OPENAI_ENDPOINT environment variable not found"
    echo "Please set it up with: export AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here"
fi

echo "Installation complete. You can now use the 'cllm' command."
echo "If 'cllm' command is not found, please run: source ~/.bashrc"