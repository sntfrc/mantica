# Mantica

**Mantica** is a web application exploring the concept of **semantic photography**: a creative and surreal fusion of human vision and AI imagination.

Inspired by the idea of looking at the world through the lens of machines, Mantica questions what it means to "see." Through semantic transformation, it becomes an artistic tool for both introspection and invention.

The web app has been mainly tested on iOS and works reasonably well on Android, but could be improved.

## Try it live
Enjoy the demo at [https://freeshell.de/sntfrc/mantica/](https://freeshell.de/sntfrc/mantica/)!

Please note that this public instance will temporarily log your original pictures for security purposes.

---

## What is semantic photography?

Mantica reimagines photography by transforming your camera shots into glimpses of alternate realities.
Here's how it works:

1. **You take a photo.**
2. The app uses an **image captioning model** to describe the content in natural language.
3. This caption is passed along with the image to an **img2img AI model**, which creatively re-renders the picture based on its understanding.

The result? A picture that is yours, and yet not yours. It's a semantic reinterpretation of what you saw, shaped by the lens of artificial imagination.

## Optional prompt control

You can guide Mantica's imagination further using a custom prompt:

Examples:
```
post-apocalyptic dreamscape, pastel colors
vaporwave aesthetic, synthwave, dark, sombre, photorealism
```

This prompt is merged with the caption before feeding it to the model.

You can also set the reinterpretation strength between 0.0 and 1.0, where 0.0 is none (regular photo) and 1.0 is a complete reimagination of the extracted description.

## General setup

1. Run ```./setup-venv.sh```
3. Create a `config` file in the repository root containing, for example:
   ```
   r8_token=YOUR_REPLICATE_TOKEN
   host=0.0.0.0
   port=8073
   logging=false
   ```
4. Start the server with `./run.sh` and open `http://localhost:8073` in your browser.
