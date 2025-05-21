Test repository to be used as a playground for the evaluation of different AI coding agents.

## Environment setup

Use `./setup-venv.sh` to create the `.venv` Python virtual environment and install the packages required by a given experiment. The script is generic and can be used for Mantica as well as future applications that may live in this repository.

## Mantica

Mantica is a small Flask application that transforms captured images using the Replicate API.

### Getting started

1. Run `./setup-venv.sh` (see **Environment setup** above) to create a Python virtual environment and install dependencies.
2. Activate the environment with `source .venv/bin/activate`.
3. Place your Replicate API token in a file named `r8_token` in the repository root.
4. Start the server with `python mantica.py` and open `http://localhost:5000` in your browser.
