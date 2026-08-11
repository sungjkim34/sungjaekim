#!/usr/bin/env python3
"""Generate the Open Graph share card (og-image.png, 1200x630).

Run from the repo root:  python3 tools/make-og-image.py

The card reuses the site's own palette and typeface so a shared link looks
like the page it points at. Regenerate whenever the name or role changes.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "og-image.png"

# Facebook/LinkedIn/Slack all crop to roughly 1.91:1; 1200x630 is the safe size.
W, H = 1200, 630
MARGIN = 90

# palette lifted from style.css
BG = "#ffffff"
HEADING = "#111114"
MUTED = "#6e6d73"
ACCENT = "#0170a3"
HAIRLINE = "#dcdbe0"

ORKNEY = ROOT / "fonts" / "orkney.otf"
FONTAWESOME = ROOT / "fonts" / "fontawesome-webfont.ttf"
FA_CODE = ""  # the </> mark used as the site logo

NAME = "Sungjae Kim"
ROLE = "STAFF MACHINE LEARNING ENGINEER"
ORG = "INTUIT  ·  DALLAS, TX"
URL = "sungjaekim.com"


def tracked(draw, xy, text, font, fill, tracking):
    """Draw text with letter-spacing. Pillow has no native tracking, so step
    through the string glyph by glyph. Returns the total advance."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x - xy[0] - tracking


def main():
    if not ORKNEY.exists():
        raise SystemExit(f"missing font: {ORKNEY}")

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    f_logo = ImageFont.truetype(str(FONTAWESOME), 58)
    f_name = ImageFont.truetype(str(ORKNEY), 116)
    f_role = ImageFont.truetype(str(ORKNEY), 30)
    f_org = ImageFont.truetype(str(ORKNEY), 22)
    f_url = ImageFont.truetype(str(ORKNEY), 22)

    # logo mark, top left
    d.text((MARGIN, MARGIN + 18), FA_CODE, font=f_logo, fill=HEADING)

    # name — the one element that has to survive being scaled down to a
    # 200px-wide thumbnail in a Slack unfurl
    name_y = 254
    d.text((MARGIN, name_y), NAME, font=f_name, fill=HEADING)

    # hairline, echoing the section rules on the site
    rule_y = name_y + 168
    d.line([(MARGIN, rule_y), (W - MARGIN, rule_y)], fill=HAIRLINE, width=2)

    # role, in the same tracked caps the site uses for labels
    tracked(d, (MARGIN, rule_y + 34), ROLE, f_role, HEADING, 3.2)
    tracked(d, (MARGIN, rule_y + 82), ORG, f_org, MUTED, 2.4)

    # accent dot + url, mirroring the "current role" node in the timeline
    dot_r = 7
    dot_cx = W - MARGIN - dot_r
    dot_cy = rule_y + 92
    url_w = d.textlength(URL, font=f_url)
    d.text((dot_cx - dot_r - 14 - url_w, dot_cy - 14), URL, font=f_url, fill=MUTED)
    d.ellipse(
        [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r],
        fill=ACCENT,
    )

    img.save(OUT, "PNG", optimize=True)
    kb = OUT.stat().st_size / 1024
    print(f"wrote {OUT.relative_to(ROOT)}  {W}x{H}  {kb:.0f} KB")


if __name__ == "__main__":
    main()
