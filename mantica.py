# Mantica - Copyright © 2025 Federico Santandrea.
# All rights reserved.
#     
# Unauthorized copying, distribution, or use of this software in whole or in part
# is prohibited without the express written permission of the copyright holder.
#
# pip install flask replicate requests pillow waitress
#

import os
import base64
import re
import replicate
import requests
import logging
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
from waitress import serve

DEFAULT_PROMPTS = [
    "turn this photograph into a painting or drawing, in the style that fits the scene the most"
]

app = Flask(__name__, template_folder=os.path.dirname(__file__))

# Load configuration (Replicate token, host and port)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config')
REPLICATE_TOKEN = None
HOST = '0.0.0.0'
PORT = 8073
WAITRESS_LOGGING = False
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if key == 'r8_token':
                REPLICATE_TOKEN = value
            elif key == 'host':
                HOST = value
            elif key == 'port':
                try:
                    PORT = int(value)
                except ValueError:
                    pass
            elif key == 'logging':
                WAITRESS_LOGGING = value.lower() == 'true'

# Default negative prompt used for image generation
NEGATIVE_PROMPT = "nsfw, naked"

# Terms removed from user prompts before sending to the model
BAN_TERMS = ["nude", "naked", "blood", "dead", "nsfw", "nude"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.path.dirname(__file__), 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory(os.path.dirname(__file__), 'service-worker.js')

@app.route('/favicon.png')
def favicon():
    return send_from_directory(os.path.dirname(__file__), 'favicon.png')

@app.route('/transform', methods=['POST'])
def transform():
    if replicate is None:
        return jsonify({'error': 'Replicate library not installed'}), 500
    data = request.get_json()
    image_data_url = data.get('image', '')
    user_prompt = data.get('prompt', '')
    logging_enabled = '!' not in user_prompt
    prompt = user_prompt.replace('!', '')

    # Remove banned terms from the prompt
    for term in BAN_TERMS:
        prompt = re.sub(r'\b' + re.escape(term) + r'\b', '', prompt, flags=re.IGNORECASE)
    prompt = ' '.join(prompt.split())

    client = replicate.Client(api_token=REPLICATE_TOKEN)

    random_prompt = DEFAULT_PROMPTS[len(image_data_url) % len(DEFAULT_PROMPTS)]
    full_prompt = prompt if prompt else random_prompt

    try:
        if "[DEBUG]" in full_prompt:
            raise Exception("debugging the safety filter")
        
        result = client.run(
            "google/nano-banana",
            input={
                "prompt": full_prompt,
                "image_input": [image_data_url],
                "aspect_ratio": "match_input_image",
                "output_format": "png"
            },
        )

        # result is usually a URL; download image
        output_url = result[0] if isinstance(result, list) else result
        transformed = requests.get(output_url).content

        out_b64 = base64.b64encode(transformed).decode('utf-8')
        problem = None

    except Exception as e:
        problem = e
        result, output_url, transformed = None, None, None

    text = full_prompt if prompt else "(no prompt)"

    if logging_enabled:
        try:
            logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            fwd_header = request.headers.get('X-Real-Ip', '')
            if fwd_header:
                ip = fwd_header
            else:
                ip = request.remote_addr or 'unknown'
            ip = ip.replace(':', '_').replace('.', '_')
            filename = f"{timestamp}-{ip}.jpg"

            # decode original image
            header, b64data = image_data_url.split(',', 1)
            orig_bytes = base64.b64decode(b64data)
            orig_img = Image.open(BytesIO(orig_bytes)).convert('RGB')

            # decode transformed image
            if transformed:
                trans_img = Image.open(BytesIO(transformed)).convert('RGB')
            else:
                trans_img = orig_img

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
            
            if problem:
                text = "[FILTER TRIGGERED] " + text

            draw = ImageDraw.Draw(collage)
            font = ImageFont.load_default()
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
    
    if not result:
        raise problem
    
    return jsonify({'image': 'data:image/png;base64,' + out_b64, 'prompt': text})


if __name__ == '__main__':
    if WAITRESS_LOGGING:
        logger = logging.getLogger('waitress')
        logger.setLevel(logging.INFO)
    serve(app, host=HOST, port=PORT)
