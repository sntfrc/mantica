import os
import base64
import tempfile
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Load Replicate token from file
TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'r8_token')
REPLICATE_TOKEN = None
if os.path.exists(TOKEN_PATH):
    with open(TOKEN_PATH, 'r') as f:
        REPLICATE_TOKEN = f.read().strip()

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
    img_data = data['image'].split(',')[1]
    prompt = data.get('prompt', '')
    strength = float(data.get('strength', 0.73))

    # Decode image data
    image_bytes = base64.b64decode(img_data)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp:
        temp.write(image_bytes)
        temp_path = temp.name

    client = replicate.Client(api_token=REPLICATE_TOKEN)

    # Example model; may need adjustment
    model = 'stability-ai/stable-diffusion-img2img'
    result = client.run(model, input={
        'image': open(temp_path, 'rb'),
        'prompt': prompt,
        'strength': strength,
    })

    # result is usually a URL; download image
    output_url = result[0] if isinstance(result, list) else result
    transformed = requests.get(output_url).content
    os.remove(temp_path)

    out_b64 = base64.b64encode(transformed).decode('utf-8')
    return jsonify({'image': 'data:image/png;base64,' + out_b64})

if __name__ == '__main__':
    app.run(debug=True)
