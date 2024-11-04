#!/bin/bash

# Install CLLM tool

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or using sudo"
    exit 1
fi

# Define the installation directory
INSTALL_DIR="/usr/local/bin"

# Copy the cllm.py script to the installation directory
if [ -f "cllm.py" ]; then
    cp cllm.py "$INSTALL_DIR/cllm"
    chmod +x "$INSTALL_DIR/cllm"
    echo "CLLM script installed successfully in $INSTALL_DIR"
else
    echo "Error: cllm.py not found in the current directory"
    exit 1
fi

# Install Python dependencies
pip install openai tiktoken gitignore_parser tqdm pyperclip

echo "CLLM dependencies installed successfully"

# Prompt user to set up Azure OpenAI credentials
echo "Please set up your Azure OpenAI credentials by running the following commands:"
echo "export AZURE_OPENAI_API_KEY=your_api_key_here"
echo "export AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here"

echo "Installation complete. You can now use the 'cllm' command."