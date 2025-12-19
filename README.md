# Mantica

**Mantica** is a web application exploring the concept of **semantic photography**: a creative and surreal fusion of human vision and AI imagination.

Inspired by the idea of looking at the world through the lens of machines, Mantica questions what it means to "see." Through semantic transformation, it becomes an artistic tool for both introspection and invention.

The web app has been mainly tested on iOS and works reasonably well on Android, but could be improved.

## Try it live
Enjoy the [live demo](https://mantica.santandrea.net/), but go easy on my wallet :)

Please note that this public instance will temporarily log your original pictures for security purposes.

---

## What is semantic photography?

Mantica reimagines photography by transforming your camera shots into glimpses of alternate realities.
Here's how it works:

1. You choose a natural language prompt.
2. You take a photo.
3. The app uses an **image to image** model to understand the content and the natural language.
4. You get a creatively remade picture.

The result? A picture that is yours, and yet not yours. It's a semantic reinterpretation of what you saw, shaped by the lens of artificial imagination.

## General setup

1. Run ```./setup-venv.sh```
3. Create a `config` file in the repository root containing, for example:
   ```
   hf_token=YOUR_HUGGINGFACE_TOKEN
   model=Qwen/Qwen-Image-Edit
   host=0.0.0.0
   port=8073
   logging=false
   ```
4. Start the server with `./run.sh` and open `http://localhost:8073` in your browser.
