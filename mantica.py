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
from flask import Flask, render_template_string, request, jsonify
from PIL import Image, ImageDraw, ImageFont
from waitress import serve

app = Flask(__name__)

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
    return render_template_string(INDEX_HTML)

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
            # Sanitize the IP address for filesystem compatibility.
            # Replace both dots and colons so IPv4/IPv6 addresses are safe.
            ip = (
                request.remote_addr or 'unknown'
            ).replace(':', '_').replace('.', '_')
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
            text = f"{full_prompt} ({strength})" if full_prompt else f"({strength})"
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

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mantica</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    body, html { margin: 0; height: 100%; font-family: Arial, sans-serif; }
    #camera { position: relative; width: 100%; height: 100%; }
    video, img { width: 100%; height: 100%; object-fit: cover; }
    #processingOverlay {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: black;
      pointer-events: none;
      opacity: 0;
      display: none;
    }
    @keyframes fadeToBlack {
      0%, 100% { opacity: 0.2; }
      50% { opacity: 0.5; }
    }
    .fade-animation {
      animation: fadeToBlack 1s infinite;
      display: block;
    }
    #controls, #after {
      position: absolute;
      bottom: 20px;
      left: 0;
      right: 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 40px;
    }
    #controls button, #after button {
      background: rgba(128,0,128,0.3);
      border: none;
      color: #fffa;
      width: clamp(50px, 15vw, 80px);
      height: clamp(50px, 15vw, 80px);
      border-radius: 50%;
      font-size: clamp(20px, 6vw, 32px);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #controls #capture {
      background: rgba(128,0,128,0.85);
      width: clamp(60px, 18vw, 96px);
      height: clamp(60px, 18vw, 96px);
      font-size: clamp(30px, 10vw, 50px);
    }
    #title { position: absolute; top: 10px; left: 10px; color: white; }
    @media (max-width: 600px) {
      #title { display:none; }
    }
    #modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); align-items: center; justify-content: center; }
    #modalContent {
      background: #222;
      padding: 20px;
      border-radius: 10px;
      color: white;
      display: flex;
      flex-direction: column;
      gap: 10px;
      position: relative;
    }
    #modalContent input[type="text"],
    #modalContent input[type="range"] {
      color: white;
      background: #333;
      border: 1px solid #555;
      border-radius: 5px;
    }
    #modalContent button {
      background: transparent;
      border: none;
      color: white;
      font-size: 24px;
    }
    #modalContent button:hover { opacity: 0.7; cursor: pointer; }
    #close {
      position: static;
    }
  </style>
</head>
<body>
  <h1 id="title">Mantica Camera</h1>
  <div id="camera">
    <video id="video" autoplay></video>
    <div id="processingOverlay"></div>
    <img id="photo" style="display:none"/>
  </div>
  <div id="controls">
    <button id="settings" aria-label="Settings"><i class="fa-solid fa-palette"></i></button>
    <button id="capture" aria-label="Take Picture"><i class="fa-solid fa-bullseye"></i></button>
    <button id="switch" aria-label="Switch Camera"><i class="fa-solid fa-camera-rotate"></i></button>
  </div>

  <div id="after" style="display:none">
    <button id="save" aria-label="Save"><i class="fa-solid fa-download"></i></button>
    <button id="back" aria-label="Back"><i class="fa-solid fa-arrow-left"></i></button>
  </div>
  <div id="promptCaption" style="display:none;position:absolute;bottom:5px;left:0;right:0;color:white;text-align:center;font-size:12px;opacity:0.8;"></div>

  <div id="modal">
    <div id="modalContent">
      <div style="display:flex;align-items:center;gap:10px;">
        <input type="text" id="prompt" placeholder="Prompt" style="flex:1">
        <button id="reset" aria-label="Reset"><i class="fa-solid fa-rotate-left"></i></button>
        <button id="close" aria-label="Close"><i class="fa-solid fa-xmark"></i></button>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <input type="range" id="strength" min="0" max="1" step="0.01" value="0.73" style="flex:1">
        <span id="strengthVal">0.73</span>
      </div>
    </div>
  </div>

<script>
let video = document.getElementById('video');
let photo = document.getElementById('photo');
let overlay = document.getElementById('processingOverlay');
let stream;
let facing = 'environment';
let promptInput = document.getElementById('prompt');
let strengthInput = document.getElementById('strength');
let strengthVal = document.getElementById('strengthVal');
let promptCaption = document.getElementById('promptCaption');

promptInput.value = localStorage.getItem('mantica_prompt') || '';
strengthInput.value = localStorage.getItem('mantica_strength') || '0.73';
strengthVal.textContent = strengthInput.value;

function isMobile() {
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

async function startCamera() {
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
  }
  stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: facing}});
  video.srcObject = stream;
  await video.play();
}

startCamera();
if (isMobile() && document.documentElement.requestFullscreen) {
  document.documentElement.requestFullscreen().catch(() => {});
}

document.getElementById('switch').onclick = () => {
  facing = facing === 'environment' ? 'user' : 'environment';
  startCamera();
};

document.getElementById('settings').onclick = () => {
  document.getElementById('modal').style.display = 'flex';
};

document.getElementById('close').onclick = () => {
  document.getElementById('modal').style.display = 'none';
};

document.getElementById('reset').onclick = () => {
  promptInput.value = '';
  strengthInput.value = 0.73;
  strengthVal.textContent = '0.73';
  localStorage.setItem('mantica_prompt', '');
  localStorage.setItem('mantica_strength', '0.73');
};

promptInput.oninput = () => {
  localStorage.setItem('mantica_prompt', promptInput.value);
};

strengthInput.oninput = (e) => {
  strengthVal.textContent = e.target.value;
  localStorage.setItem('mantica_strength', e.target.value);
};

document.getElementById('capture').onclick = async () => {
  overlay.classList.add('fade-animation');
  document.getElementById('controls').style.display = 'none';
  document.getElementById('after').style.display = 'none';
  overlay.style.display = 'block';
  // Let the DOM update so the buttons disappear before heavy processing
  await new Promise(requestAnimationFrame);
  video.pause();
  let canvas = document.createElement('canvas');
  const displayWidth = video.clientWidth;
  const displayHeight = video.clientHeight;
  canvas.width = displayWidth;
  canvas.height = displayHeight;

  const vw = video.videoWidth;
  const vh = video.videoHeight;
  const elementRatio = displayWidth / displayHeight;
  const videoRatio = vw / vh;

  let sx = 0, sy = 0, sWidth = vw, sHeight = vh;
  if (videoRatio > elementRatio) {
    // Video is wider than the display area; crop the sides
    sWidth = vh * elementRatio;
    sx = (vw - sWidth) / 2;
  } else {
    // Video is taller than the display area; crop the top and bottom
    sHeight = vw / elementRatio;
    sy = (vh - sHeight) / 2;
  }
  canvas.getContext('2d').drawImage(
    video,
    sx,
    sy,
    sWidth,
    sHeight,
    0,
    0,
    displayWidth,
    displayHeight
  );
  let dataUrl = canvas.toDataURL('image/png');
  let prompt = promptInput.value;
  let strength = strengthInput.value;

  try {
    let res = await fetch('/transform', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({image: dataUrl, prompt: prompt, strength: strength})
    });
    let json = await res.json();
    if (!res.ok || json.error) throw new Error(json.error || 'processing error');
    photo.src = json.image;
    video.style.display = 'none';
    photo.style.display = 'block';
    document.getElementById('after').style.display = 'flex';
    promptCaption.textContent = json.prompt || '';
    promptCaption.style.display = json.prompt ? 'block' : 'none';
  } catch (e) {
    console.error(e);
    video.play();
    document.getElementById('controls').style.display = 'flex';
  }
  overlay.classList.remove('fade-animation');
  overlay.style.display = 'none';
};

document.getElementById('back').onclick = () => {
  photo.style.display = 'none';
  video.style.display = 'block';
  document.getElementById('after').style.display = 'none';
  document.getElementById('controls').style.display = 'flex';
  promptCaption.style.display = 'none';
  video.play();
};

document.getElementById('save').onclick = () => {
  let a = document.createElement('a');
  a.href = photo.src;
  const now = new Date();
  const pad = n => n.toString().padStart(2, '0');
  const ts =
    now.getFullYear().toString() +
    pad(now.getMonth() + 1) +
    pad(now.getDate()) +
    '-' +
    pad(now.getHours()) +
    pad(now.getMinutes()) +
    pad(now.getSeconds());
  a.download = `mantica-${ts}.png`;
  a.click();
};
</script>
</body>
</html>
"""

if __name__ == '__main__':
    if WAITRESS_LOGGING:
        logging.basicConfig(level=logging.INFO)
    serve(app, host=HOST, port=PORT)
