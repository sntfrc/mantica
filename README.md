Test repository to be used as a playground for the evaluation of different AI coding agents.

## General setup

1. Run `./setup-venv.sh` to create a Python virtual environment and install dependencies.
2. Activate the environment with `source .venv/bin/activate`.

## Mantica

Mantica is a small Flask application that transforms captured images using the Replicate API.

1. Place your Replicate API token in a file named `r8_token` in the repository root.
2. Start the server with `python mantica.py` and open `http://localhost:5000` in your browser.
