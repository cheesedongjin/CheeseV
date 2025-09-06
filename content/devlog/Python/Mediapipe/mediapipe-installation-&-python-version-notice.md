# Mediapipe Installation & Python Version Notice

*2025-07-29*

## Overview

Installing Mediapipe via `pip install mediapipe` may fail due to Python version compatibility.

## Supported Python Versions

- Works on **Python 3.7** and **Python 3.8**  
- **pip install mediapipe** will currently **not** work with Python **3.9** or higher

## Installation Example

```bash
# Create a Python 3.8 virtual environment
python3.8 -m venv mediapipe-env
source mediapipe-env/bin/activate

# Install Mediapipe
pip install mediapipe
```
