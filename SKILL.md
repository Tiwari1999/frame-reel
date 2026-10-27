---
name: frame-reel
description: Make a short video (Instagram Reel, TikTok, Short, launch clip) from code, one frame at a time. An HTML page draws every frame as a pure function of time, Playwright screenshots each one, numpy synthesises the music and ffmpeg stitches the mp4. Use when asked to make a reel, a motion graphic or a launch video without a video editor.
---

# frame-reel

Claude can't drag clips on a timeline, but it can write a page that draws frame N. This skill is that loop:

1. **Engine.** `comp.html` defines `window.render(t)`. `scripts/render.py` calls it for every frame and screenshots the page. `scripts/mux.sh` stitches the JPGs and the music into an mp4.
2. **Real references.** Colours, fonts and screenshots come from the actual product or brand before any layout is written.
3. **Self-check.** Stills from every scene go onto one contact sheet, and you look at it before the full render.

Requirements: Python 3.10+, `pip install playwright numpy scipy pillow`, `playwright install chromium`, and ffmpeg on the PATH (or set `FFMPEG`). The scripts live in `scripts/` next to this file.

## 1. Plan on a beat grid

Pick the tempo first, then put every cut on a bar line. At 96 BPM a bar is 2.5 s; at 120 BPM it is 2 s. Write the scene list with start and end times that sum to the target length (15 to 45 s for a Reel).

Hook in the first 2 seconds, one idea per scene, and a frame that changes at least every 4 seconds.

## 2. Collect real references

Before any layout: exact hex colours, font names, and two or three screenshots of the real thing. Put them at the top of the composition as CSS tokens. Without references the output drifts to purple gradients and rocket emoji, so if the user gives none, ask for them or read them from the project's own CSS.

## 3. Write `comp.html`

- The page is the frame: 1080x1920 by default (change `W, H` in `render.py` for other sizes).
- `window.render(t)` sets every element's state from `t` alone. No CSS transitions or animations, no `setTimeout`, no `requestAnimationFrame`, no `Date.now()`, and no unseeded `Math.random()`. Same `t`, same pixels, so any frame can be re-rendered on its own.
- `window.__ready` is a promise that resolves after fonts and images have loaded: call `document.fonts.load()` for each face you use, then `await imgReady()`.
- Load `scripts/engine.js` for the helpers: `S(t, a, b)` progress, the easings `out3`, `inout` and `back`, `vis(t, a, b)` for scene fades, and `words()` plus `stagger()` for headlines that rise in word by word.
- **Safe zone for Reels:** keep text between y=250 and y=1440, and keep the right 230 px clear below y=1000, where the like and comment buttons sit.
- **Readability:** any line meant to be read stays fully on screen for about 0.3 s per word.
- **Transitions:** dip out and back in (`vis` does this), never a plain crossfade between two busy layouts.

`example/comp.html` is a complete 6-second composition to copy from.

## 4. Look at stills before the full render

```bash
python scripts/render.py comp.html 30 stills 2,6.5,9.8,13.7,18.6,24 stills/
python scripts/sheet.py stills/ sheet.jpg
```

Open `sheet.jpg` and look at it. Include stills from mid-transition as well as settled frames. Check for:

- text outside the safe zone, or clipped
- a word alone on the last line of a headline
- elements colliding, or low contrast
- anything that only reads at desktop size

Fix the composition, render the stills again, and repeat until the sheet is clean.

## 5. Render, score, mux

```bash
python scripts/render.py comp.html 30 all frames/      # 900 JPGs, f0000.jpg ...
python music.py music.wav                             # your score, built on scripts/synth.py
scripts/mux.sh frames music.wav reel.mp4              # H.264 CRF 18, AAC 192k, -14 LUFS
```

On an Apple M3 Pro, 900 frames at 1080x1920 rendered in 41 to 51 s.

**Music.** `scripts/synth.py` has a `Score(dur)` with five buses (drums, bass, pad, pluck, sfx). Its instruments are `kick`, `clap`, `hat`, `bass_note`, `pad_chord`, `pluck_note`, `bell`, `tick`, `key_tick`, `swish` and `sub_hit`, plus a `groove()` helper. `mix()` levels each bus against a reference window, ducks the bass under the kicks, adds a small room and soft-clips. Put every hit on the same grid as the cuts, so the sound effects land with the picture. `example/music.py` shows the shape.

## 6. Deliver

- Pull a settled frame with the hook fully on screen as the cover: `ffmpeg -ss 3 -i reel.mp4 -frames:v 1 cover.jpg`.
- Check loudness: `ffmpeg -i reel.mp4 -af ebur128 -f null -` should report about -14 LUFS.
- Keep `frames/`, `stills/` and `music.wav` out of git. They rebuild from the composition.
