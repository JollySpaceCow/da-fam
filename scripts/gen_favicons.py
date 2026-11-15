#!/usr/bin/env python3
"""
Generate favicon assets using the actual Fraunces font via ImageMagick.
Colours match the da-fam palette:
  bg  #101715   text #EFE8D8 (parchment - same as page title)

Run once; commit the outputs; delete this script if desired.
"""

import os, struct, subprocess, zlib, shutil

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT   = os.path.join(ROOT, "assets")
FONT  = "/tmp/fraunces-600.ttf"   # downloaded by agent
MAGICK = shutil.which("magick") or shutil.which("convert")

BG    = "#101715"
TEXT  = "#EFE8D8"   # --parchment, same as the h1 colour in the page

def render_png(path, size):
    """
    Render "DF" in Fraunces at the given size using ImageMagick.
    Letters slightly overlap (negative letter-spacing via manual positioning).
    We render at 2× then resize down for anti-aliasing.
    """
    render_size = size * 4          # render big, downsample for quality
    r = render_size
    corner  = int(r * 0.22)         # rounded corner radius

    # font size: fill ~72% of the icon height
    font_pt = int(r * 0.62)

    # We place "D" and "F" as separate -annotate calls so we can nudge them
    # together. Overlap = ~8% of render size.
    overlap = int(r * 0.08)

    # Total text width ≈ 2 glyphs - overlap; centre on canvas.
    # We use gravity West/East relative to centre, offset by overlap/2 each way.
    half = r // 2

    cmd = [
        MAGICK,
        "-size", f"{r}x{r}",
        f"xc:{BG}",
        # Rounded corners via rounded rectangle mask
        "(",
            "+clone",
            "-alpha", "extract",
            "-draw", f"roundrectangle 0,0,{r-1},{r-1},{corner},{corner}",
            "-negate",
            "-threshold", "0",
            "-negate",
        ")",
        "-alpha", "off",
        "-compose", "CopyOpacity",
        "-composite",
        # Draw "D" slightly right of left-centre
        "-font", FONT,
        "-pointsize", str(font_pt),
        "-fill", TEXT,
        "-gravity", "Center",
        "-annotate", f"+{-overlap // 2 - int(r*0.1)}+{int(r*0.04)}", "D",
        # Draw "F" slightly left of right-centre (overlapping D)
        "-annotate", f"+{overlap // 2 + int(r*0.1)}+{int(r*0.04)}", "F",
        # Resize down with Lanczos for crisp edges
        "-resize", f"{size}x{size}",
        "-strip",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[:200]}")
        return False
    print(f"{os.path.basename(path)} ({size}×{size}) ✓")
    return True


# ── SVG favicon (references font via @font-face for modern browsers) ──────────
SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&amp;display=swap');
    </style>
  </defs>
  <rect width="64" height="64" rx="14" fill="#101715"/>
  <!-- D and F overlap slightly: D at x=18, F at x=36 (width ~20px each at this scale) -->
  <text y="47"
        font-family="Fraunces, Georgia, serif"
        font-weight="600"
        font-size="34"
        fill="#EFE8D8">
    <tspan x="10">D</tspan><tspan dx="-6">F</tspan>
  </text>
</svg>
"""
with open(os.path.join(OUT, "favicon.svg"), "w") as f:
    f.write(SVG)
print("favicon.svg ✓")


# ── PNG sizes ─────────────────────────────────────────────────────────────────
sizes = {
    "favicon-16x16.png":  16,
    "favicon-32x32.png":  32,
    "favicon-48x48.png":  48,
    "apple-touch-icon.png": 180,
}
for name, size in sizes.items():
    render_png(os.path.join(OUT, name), size)


# ── favicon.ico — bundle 16, 32, 48 PNGs ─────────────────────────────────────
def _chunk(tag, data):
    c = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", c)

ico_sizes = [16, 32, 48]
png_blobs = []
for s in ico_sizes:
    p = os.path.join(OUT, f"favicon-{s}x{s}.png")
    with open(p, "rb") as f:
        png_blobs.append(f.read())

n = len(ico_sizes)
header_size = 6 + n * 16
offsets, off = [], header_size
for blob in png_blobs:
    offsets.append(off); off += len(blob)

ico  = struct.pack("<HHH", 0, 1, n)
for i, s in enumerate(ico_sizes):
    ico += struct.pack("<BBBBHHII",
        s if s < 256 else 0, s if s < 256 else 0,
        0, 0, 1, 32,
        len(png_blobs[i]), offsets[i])
for blob in png_blobs:
    ico += blob

with open(os.path.join(OUT, "favicon.ico"), "wb") as f:
    f.write(ico)
print("favicon.ico (16/32/48) ✓")


# ── site.webmanifest ──────────────────────────────────────────────────────────
manifest = """\
{
  "name": "Da Fam'",
  "short_name": "Da Fam'",
  "description": "Your private family tree — everything stays on your device.",
  "start_url": "../",
  "display": "standalone",
  "background_color": "#101715",
  "theme_color": "#101715",
  "icons": [
    { "src": "favicon-32x32.png",    "sizes": "32x32",   "type": "image/png" },
    { "src": "favicon-48x48.png",    "sizes": "48x48",   "type": "image/png" },
    { "src": "apple-touch-icon.png", "sizes": "180x180", "type": "image/png" }
  ]
}
"""
with open(os.path.join(OUT, "site.webmanifest"), "w") as f:
    f.write(manifest)
print("site.webmanifest ✓")


# ── sitemap.xml ───────────────────────────────────────────────────────────────
sitemap = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://jollyspacecow.github.io/da-fam/</loc>
    <lastmod>2026-11-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
    f.write(sitemap)
print("sitemap.xml ✓")

print("\nAll assets generated.")
