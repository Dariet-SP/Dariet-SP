# Producción del reel – Posicionador PROMED

- `reel3.html`: escenas del reel (desde "Precisión y consistencia" hasta el cierre), sincronizadas con `assets/voz_elevenlabs_v3.mp3`. Se renderiza cuadro a cuadro con `shoot3.js` (Playwright) llamando a `render(t)`.
- `usage_front_closeup/`: animación ilustrada de uso (borrador).
- `assets/`: recortes del producto mejorados con IA (Real-ESRGAN + BiRefNet), logos y voz.
- `music2.py`: genera la música original.
- Fuentes: `npm i @fontsource/montserrat` dentro de una carpeta `build/` al mismo nivel que esta carpeta (ruta `../build/node_modules/...`).
