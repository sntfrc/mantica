# Mantica

**Mantica** is a web application exploring the concept of **semantic photography**: a creative and surreal fusion of human vision and AI imagination.

Inspired by the idea of looking at the world through the lens of machines, Mantica questions what it means to "see." Through semantic transformation, it becomes an artistic tool for both introspection and invention.

The web app has been mainly tested on iOS and works reasonably well on Android, but could be improved.

## Try it live
Enjoy the demo at [mantica.santandrea.net](https://mantica.santandrea.net). Be easy on my wallet :)

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

```
[number:]your prompt here
```

- `number` (optional): how strong the AI's imaginative transformation should be (e.g., 0 = very close to original, 15 = very wild).
- `your prompt here`: acts as an **addendum** to the image captioning model output, steering the output style.

Examples:
```
post-apocalyptic dreamscape, pastel colors
97:vaporwave aesthetic, synthwave, dark, sombre, photorealism
```

This prompt is merged with the caption before feeding it to the model.
