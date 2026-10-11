# Producción de reels PROMED

Fuentes del reel del posicionador. Úsalas como plantilla para otros productos. Las reglas de marca, el tono y el flujo completo están en `../PROMPT_MAESTRO_VIDEOS_PROMED.md`.

## Estructura
- `assets/`: recortes limpios del producto (Real-ESRGAN + BiRefNet), logos, textura de grano y la voz de ElevenLabs v3.
- `educativo/`
  - `usage_src.html`: animación de uso. `build.py` la convierte en `usage_final.html` con las fuentes embebidas, y `shoot.js frames <dir> 324 30` la renderiza.
  - `reel3_escenas.html`: escenas desde "Precisión y consistencia" hasta el cierre. Los tiempos están fijados en segundos absolutos de la voz v3.
  - `music3.py`: música (duración como argumento).
- `fondo_claro/`
  - `reel2.html`: reel dinámico de fondo claro. Los tiempos se cargan desde `timing.json` (`window.TIMING`).
  - `shoot2.js`: render (`node shoot2.js full <dir>`).
  - `music2.py`: música.
- `tools/audio/`
  - `duck.py`: reduce la música bajo la voz, con anticipación.
  - `sepcheck.py`: mide el margen voz/música.
  - `mixit.sh`: mezcla alternativa con sidechain.
  - `transcribir_whisper.py`: transcribe con Whisper.
  - `voz_provisional_piper.py`: genera una voz temporal con Piper y elige la mejor toma con Whisper.
- `tools/imagen/`
  - `ff.py`: emparejado del fondo.
  - `rb.py`: recorte con rembg/BiRefNet.
  - `clips.py`: limpieza de clips de video.
  - `enhance/`: pipeline de super-resolución + recorte refinado (scripts de referencia; ajusta las rutas `./trabajo` y `./fotos_originales`).
- `tools/render/`: renderizadores con Playwright, por rango de tiempo (`shoot_rango.js`) o por `timing.json` (`shoot_timing.js`).

## Puesta en marcha
```bash
npm install && npx playwright install chromium
pip install numpy pillow scipy soundfile onnxruntime "rembg[cpu]" sherpa-onnx
```
Los HTML buscan las fuentes en `../node_modules/@fontsource/montserrat/files/` y las imágenes en `../assets/`.
