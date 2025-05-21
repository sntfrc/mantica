import os
import base64
import re
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw, ImageFont

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
    user_prompt = data.get('prompt', '')
    logging_enabled = '!' not in user_prompt
    prompt = user_prompt.replace('!', '')
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

    if logging_enabled:
        try:
            logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            ip = (request.remote_addr or 'unknown').replace(':', '-')
            filename = f"{timestamp}-{ip}.jpg"

            # decode original image
            header, b64data = image_data_url.split(',', 1)
            orig_bytes = base64.b64decode(b64data)
            orig_img = Image.open(BytesIO(orig_bytes)).convert('RGB')
            trans_img = Image.open(BytesIO(transformed)).convert('RGB')

            landscape = orig_img.width >= orig_img.height and trans_img.width >= trans_img.height
            if landscape:
                collage_width = max(orig_img.width, trans_img.width)
                collage_height = orig_img.height + trans_img.height
                collage = Image.new('RGB', (collage_width, collage_height))
                collage.paste(orig_img, (0, 0))
                collage.paste(trans_img, (0, orig_img.height))
            else:
                collage_width = orig_img.width + trans_img.width
                collage_height = max(orig_img.height, trans_img.height)
                collage = Image.new('RGB', (collage_width, collage_height))
                collage.paste(orig_img, (0, 0))
                collage.paste(trans_img, (orig_img.width, 0))

            draw = ImageDraw.Draw(collage)
            font = ImageFont.load_default()
            text = full_prompt
            if hasattr(draw, "textbbox"):
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width, text_height = draw.textsize(text, font=font)
            padding = 5
            final_img = Image.new(
                'RGB', (collage_width, collage_height + text_height + 2 * padding), color='black'
            )
            final_img.paste(collage, (0, 0))
            draw = ImageDraw.Draw(final_img)
            draw.text(
                ((collage_width - text_width) // 2, collage_height + padding),
                text,
                fill='white',
                font=font,
            )
            final_img.save(os.path.join(logs_dir, filename), format='JPEG')
        except Exception as e:
            print('Logging failed:', e)

    return jsonify({'image': 'data:image/png;base64,' + out_b64, 'prompt': full_prompt})

if __name__ == '__main__':
    app.run(debug=True)
