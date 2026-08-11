#!/usr/bin/env python3
"""Generate the favicon set, plus a comparison sheet for choosing a variant.

  python3 tools/make-favicon.py --preview <dir>   # contact sheet only
  python3 tools/make-favicon.py --variant s-blue  # write the real files

Design notes: the tile is filled rather than transparent so the icon carries
its own background — a bare dark glyph vanishes against the dark tab strip
browsers use in dark mode. Masters are drawn at 512px and downsampled with
LANCZOS; drawing directly at 16px produces mush.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ORKNEY = ROOT / "fonts" / "orkney.otf"

ACCENT = "#0170a3"
INK = "#111114"
WHITE = "#ffffff"

MASTER = 512
ICO_SIZES = [16, 32, 48]
APPLE = 180

VARIANTS = {
    "s-blue": {"bg": ACCENT, "fg": WHITE, "kind": "text", "text": "S"},
    "s-ink": {"bg": INK, "fg": WHITE, "kind": "text", "text": "S"},
    "code-blue": {"bg": ACCENT, "fg": WHITE, "kind": "chevrons"},
    "sk-blue": {"bg": ACCENT, "fg": WHITE, "kind": "text", "text": "SK"},
}


def draw_master(spec):
    S = MASTER
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=spec["bg"])

    if spec["kind"] == "text":
        text = spec["text"]
        # size the glyph so its ink box is ~54% of the tile (46% for two chars)
        target = S * (0.46 if len(text) > 1 else 0.54)
        size = int(S * 0.6)
        for _ in range(40):
            f = ImageFont.truetype(str(ORKNEY), size)
            box = d.textbbox((0, 0), text, font=f)
            h = box[3] - box[1]
            if abs(h - target) <= 2:
                break
            size = max(8, int(size * (target / max(h, 1))))
        f = ImageFont.truetype(str(ORKNEY), size)
        box = d.textbbox((0, 0), text, font=f)
        # centre on the ink box, not the line box, so it sits optically centred
        x = (S - (box[2] - box[0])) / 2 - box[0]
        y = (S - (box[3] - box[1])) / 2 - box[1]
        d.text((x, y), text, font=f, fill=spec["fg"])

    else:  # chevrons — the masthead </> mark reduced to <> so it holds at 16px
        w = int(S * 0.085)
        cy = S / 2
        half_h = S * 0.17
        inner, outer = S * 0.30, S * 0.46
        d.line([(outer, cy - half_h), (inner, cy), (outer, cy + half_h)],
               fill=spec["fg"], width=w, joint="curve")
        d.line([(S - outer, cy - half_h), (S - inner, cy), (S - outer, cy + half_h)],
               fill=spec["fg"], width=w, joint="curve")
    return img


def down(img, n):
    return img.resize((n, n), Image.LANCZOS)


def glyph_path(text, target_h):
    """Convert text to an SVG path via the actual Orkney outlines.

    An SVG favicon renders in an isolated context with no access to the page's
    @font-face, so a <text> element would silently fall back to Helvetica and
    stop matching the ICO. Outlines remove the font dependency entirely.
    """
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont

    font = TTFont(str(ORKNEY))
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()

    # lay the glyphs out on a shared baseline, advancing by each one's width
    combined, x = [], 0.0
    for ch in text:
        name = cmap[ord(ch)]
        combined.append((name, x))
        x += gs[name].width

    bounds = BoundsPen(gs)
    for name, dx in combined:
        from fontTools.misc.transform import Transform
        gs[name].draw(TransformPen(bounds, Transform().translate(dx, 0)))
    x0, y0, x1, y1 = bounds.bounds

    scale = target_h / (y1 - y0)
    # flip Y (font space is up-positive, SVG is down-positive) and centre on
    # the ink box so the mark sits optically centred in the tile
    tx = 50 - ((x0 + x1) / 2) * scale
    ty = 50 + ((y0 + y1) / 2) * scale

    pen = SVGPathPen(gs)
    for name, dx in combined:
        from fontTools.misc.transform import Transform
        gs[name].draw(TransformPen(pen, Transform().translate(dx, 0)))
    return pen.getCommands(), tx, ty, scale


def svg_for(spec):
    if spec["kind"] == "text":
        d_attr, tx, ty, s = glyph_path(spec["text"],
                                       54 if len(spec["text"]) == 1 else 46)
        inner = (f'<path d="{d_attr}" fill="{spec["fg"]}" '
                 f'transform="translate({tx:.3f} {ty:.3f}) scale({s:.6f} {-s:.6f})"/>')
    else:
        inner = (f'<g fill="none" stroke="{spec["fg"]}" stroke-width="8.5" '
                 f'stroke-linecap="round" stroke-linejoin="round">'
                 f'<polyline points="46,33 30,50 46,67"/>'
                 f'<polyline points="54,33 70,50 54,67"/></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            f'<rect width="100" height="100" rx="22" fill="{spec["bg"]}"/>{inner}</svg>')


def preview(outdir):
    outdir = Path(outdir)
    names = list(VARIANTS)
    pad, col = 26, 210
    sheet = Image.new("RGB", (pad * 2 + col * len(names), 470), "#ffffff")
    d = ImageDraw.Draw(sheet)
    label = ImageFont.truetype(str(ORKNEY), 17)
    small = ImageFont.truetype(str(ORKNEY), 13)

    for i, name in enumerate(names):
        m = draw_master(VARIANTS[name])
        x = pad + i * col
        d.text((x, 18), name, font=label, fill="#111114")
        # 32px, zoomed 4x, nearest so you see the real pixels
        sheet.paste(down(m, 32).resize((128, 128), Image.NEAREST), (x, 48))
        d.text((x, 184), "32px @4x", font=small, fill="#6e6d73")
        # 16px, zoomed 8x
        sheet.paste(down(m, 16).resize((128, 128), Image.NEAREST), (x, 210))
        d.text((x, 346), "16px @8x", font=small, fill="#6e6d73")

    # the real test: actual 16px against light and dark tab strips
    for j, (bg, fg, cap) in enumerate([("#f1f3f4", "#111114", "light tab strip"),
                                       ("#202124", "#e8eaed", "dark tab strip")]):
        y = 378 + j * 44
        d.rectangle([pad, y, sheet.width - pad, y + 34], fill=bg)
        d.text((pad + 10, y + 9), cap, font=small, fill=fg)
        for i, name in enumerate(names):
            ic = down(draw_master(VARIANTS[name]), 16)
            sheet.paste(ic, (pad + 150 + i * 60, y + 9), ic)

    p = outdir / "favicon-variants.png"
    sheet.save(p)
    print(f"wrote {p}")


def build(variant):
    spec = VARIANTS[variant]
    m = draw_master(spec)
    frames = [down(m, n) for n in ICO_SIZES]
    frames[-1].save(ROOT / "favicon.ico", format="ICO",
                    sizes=[(n, n) for n in ICO_SIZES])
    down(m, APPLE).convert("RGB").save(ROOT / "apple-touch-icon.png", optimize=True)
    (ROOT / "favicon.svg").write_text(svg_for(spec))
    for f in ("favicon.ico", "apple-touch-icon.png", "favicon.svg"):
        print(f"  {f}  {(ROOT / f).stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--variant", choices=list(VARIANTS))
    a = ap.parse_args()
    if a.preview:
        preview(a.preview)
    elif a.variant:
        build(a.variant)
    else:
        ap.error("pass --preview <dir> or --variant <name>")
