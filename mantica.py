import os
import base64
import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Load Replicate token from file
TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'r8_token')
REPLICATE_TOKEN = None
if os.path.exists(TOKEN_PATH):
    with open(TOKEN_PATH, 'r') as f:
        REPLICATE_TOKEN = f.read().strip()

# Default negative prompt used for image generation
NEGATIVE_PROMPT = "nsfw, naked"

# Terms removed from user prompts before sending to the model
BAN_TERMS = ["nude", "naked", "blood", "dead", "nsfw", "nude"]

try:
    import replicate
    import requests
except ImportError:
    replicate = None
    requests = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transform', methods=['POST'])
def transform():
    if replicate is None:
        return jsonify({'error': 'Replicate library not installed'}), 500
    data = request.get_json()
    image_data_url = data.get('image', '')
    prompt = data.get('prompt', '')
    strength = float(data.get('strength', 0.73))

    # Remove banned terms from the prompt
    for term in BAN_TERMS:
        prompt = re.sub(r'\b' + re.escape(term) + r'\b', '', prompt, flags=re.IGNORECASE)
    prompt = ' '.join(prompt.split())

    client = replicate.Client(api_token=REPLICATE_TOKEN)

    # Use BLIP to generate an image caption first
    caption = client.run(
        "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
        input={"image": image_data_url, "task": "image_captioning"},
    )

    if isinstance(caption, list):
        caption = caption[0]
    caption = caption or ""
    if caption.lower().startswith("caption:"):
        caption = caption[len("caption:"):].strip()

    # Append the user prompt to the caption
    full_prompt = caption
    if prompt:
        if full_prompt:
            full_prompt += ", " + prompt
        else:
            full_prompt = prompt

    # Parameters tuned similarly to the PHP version
    result = client.run(
        "black-forest-labs/flux-dev",
        input={
            "prompt": full_prompt,
            "aspect_ratio": "1:1",
            "image": image_data_url,
            "prompt_strength": strength,
            "num_outputs": 1,
            "num_inference_steps": 28,
            "guidance": 3.5,
            "output_format": "png",
            "output_quality": 100,
            "negative_prompt": NEGATIVE_PROMPT,
            "go_fast": True,
        },
    )

    # result is usually a URL; download image
    output_url = result[0] if isinstance(result, list) else result
    transformed = requests.get(output_url).content

    out_b64 = base64.b64encode(transformed).decode('utf-8')
    return jsonify({'image': 'data:image/png;base64,' + out_b64, 'prompt': full_prompt})

if __name__ == '__main__':
    app.run(debug=True)
