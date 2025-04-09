#!/bin/bash
set -e

echo "This script will set up a Python development environment using:"
echo "- conda if it's available in your PATH"
echo "- venv if conda is not found"
echo "Both options will install the same dependencies from pyproject.toml"
echo

read -p "Would you like to continue? [y/N] " response
if [[ ! $response =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 1
fi

# Determine if using conda or venv
if command -v conda &> /dev/null; then
    echo "Setting up conda environment..."
    
    # Check if environment exists
    if conda env list | grep -q "^cllm "; then
        echo "Environment 'cllm' already exists, updating..."
        conda activate cllm
        conda update --all -y  # Update all packages in the environment
    else
        echo "Creating new environment 'cllm'..."
        conda create -n cllm python=3.10 -y
        conda activate cllm
    fi
    
    # Install/update dependencies
    pip install -e ".[dev]"
else
    echo "Setting up venv environment..."
    
    # Check if environment exists
    if [ -d ".venv" ]; then
        echo "Virtual environment already exists, updating..."
        source .venv/bin/activate
        pip install --upgrade pip
    else
        echo "Creating new virtual environment..."
        python3.10 -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip
    fi
    
    pip install -e ".[dev]"
fi

# Verify installation
python -c "import rdflib; print(f'rdflib {rdflib.__version__}')"
python -c "import flake8; print(f'flake8 {flake8.__version__}')"

echo "Development environment setup complete!"
echo "To activate:"
echo "  conda: conda activate cllm"
echo "  venv:  source .venv/bin/activate" 