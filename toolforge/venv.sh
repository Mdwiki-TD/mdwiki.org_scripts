#!/bin/bash

# Define virtual environment directories
WWW_VENV_DIR="www/python/venv"
VENV_DIR=".venv"

# Check if WWW_VENV_DIR exists (read-only, do not create)
if [ -d "$WWW_VENV_DIR" ]; then
    echo "Found WWW virtual environment. Activating..."
    source "$WWW_VENV_DIR/bin/activate"

# Fallback to VENV_DIR (check if exists or create)
elif [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists in $VENV_DIR. Activating..."
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found. Creating in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"

    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Upgrade pip to the latest version
    echo "Upgrading pip..."
    pip install --upgrade pip

    # Install requirements if the file exists
    if [ -f "requirements.txt" ]; then
        echo "Installing requirements.txt..."
        pip install -r requirements.txt
    fi

    # Install development requirements if the file exists
    if [ -f "dev-requirements.txt" ]; then
        echo "Installing dev-requirements.txt..."
        pip install -r dev-requirements.txt
    fi

    echo "Setup and installation completed successfully!"
fi
