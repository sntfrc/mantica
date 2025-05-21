Test repository to be used as a playground for the evaluation of different AI coding agents.

## General setup

1. Run `./setup-venv.sh` to create a Python virtual environment and install dependencies.
2. Activate the environment with `source .venv/bin/activate`.

## Mantica

Mantica is a small Flask application that transforms captured images using the Replicate API.

1. Create a `config` file in the repository root containing:

   ```
   r8_token=YOUR_REPLICATE_TOKEN
   host=0.0.0.0
   port=8073
   ```

2. Start the server with `python mantica.py` and open `http://localhost:8073` in your browser. The script uses the Waitress WSGI server.
