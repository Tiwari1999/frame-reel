"""Render a reel composition: `render.py COMP.html DUR stills t,t,... OUTDIR` or `render.py COMP.html DUR all OUTDIR`.
Each frame is window.render(t), awaited, then screenshotted at W x H (1080x1920 vertical by default)."""
import asyncio, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

W, H, FPS = 1080, 1920, 30   # change W, H for landscape (1920, 1080) or square (1080, 1080)

async def main(comp, dur, mode, arg, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--font-render-hinting=none", "--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        await pg.goto(Path(comp).resolve().as_uri(), wait_until="load")
        await pg.evaluate("window.__ready")
        if mode == "stills":
            for t in [float(x) for x in arg.split(",")]:
                await pg.evaluate(f"render({t})")
                await pg.screenshot(path=str(out / f"t{t:05.2f}.png"))
        else:
            n, t0 = int(round(dur * FPS)), time.time()
            for f in range(n):
                await pg.evaluate(f"render({f / FPS})")
                await pg.screenshot(path=str(out / f"f{f:04d}.jpg"), type="jpeg", quality=93)
                if f % 150 == 0:
                    print(f"frame {f}/{n}  {time.time() - t0:.0f}s", flush=True)
        if errs:
            print("PAGE ERRORS:", *errs[:10], sep="\n  ")
        await b.close()

comp, dur, mode = sys.argv[1], float(sys.argv[2]), sys.argv[3]
asyncio.run(main(comp, dur, mode, sys.argv[4] if mode == "stills" else None, sys.argv[-1]))
