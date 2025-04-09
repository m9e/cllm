#!/usr/bin/env bash
set -euo pipefail

# Help message
show_help() {
    echo "Usage: $0 [--system]"
    echo "Install CLLM using pipx"
    echo ""
    echo "Options:"
    echo "  --system    Install system-wide (requires root privileges)"
    exit 0
}

# Parse arguments
SYSTEM_WIDE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            ;;
        --system)
            SYSTEM_WIDE=true
            shift
            ;;
        *)
            echo "Error: Unknown option: $1"
            show_help
            ;;
    esac
done

# Check for pipx
if ! command -v pipx >/dev/null 2>&1; then
    echo "Error: pipx is required but not installed."
    echo "Please install pipx first:"
    echo "  pip install --user pipx"
    echo "  pipx ensurepath"
    exit 1
fi

# Install CLLM
if [ "$SYSTEM_WIDE" = true ]; then
    if [ "$(id -u)" -ne 0 ]; then
        echo "Error: System-wide installation requires root privileges."
        echo "Please run with sudo."
        exit 1
    fi
    echo "Installing CLLM system-wide..."
    pipx install --system-site-packages .
else
    echo "Installing CLLM for current user..."
    pipx install .
fi

echo "Installation complete!"
echo ""
echo "Next Steps:"
echo "1. Configure Azure OpenAI credentials using either:"
echo "   - Run: ./configure_cllm.sh --azure-key YOUR_KEY --azure-endpoint YOUR_ENDPOINT"
echo "   - Or manually set environment variables (see README.md)"
echo ""
echo "For detailed instructions on getting your Azure OpenAI credentials,"
echo "please refer to the 'Azure OpenAI Configuration' section in README.md"

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