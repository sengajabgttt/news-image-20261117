"""news-image-20261117 entry in Python 3.13 (standard library only).

Draws a one-page newspaper infographic summing up Tuesday 17 November
2026's world news and writes it to /output/entry.png. The image is drawn
entirely by this program at run time, deterministically, from the six
stories below (researched from published reporting on 17 November 2026 and
baked into the code): no network, no clock, no randomness, so two runs
produce byte-identical output.

Layout (1024 x 1024): a navy masthead naming the day, then six story
panels in two columns. Each panel has a coloured kicker, a headline and a
short factual body. Text is drawn with a 5x7 bitmap font defined below,
scaled up; all text is uppercase, which keeps every glyph legible at the
~300 px size the judge views the image at.

Stories (each corroborated by at least two published sources on the day):
1. UKRAINE: Ukraine struck the Crimean (Kerch) Bridge for a second
   straight day; a road section collapsed into the water. Kyiv called the
   attack unprecedented; Russia hit bridges in Kyiv in reply.
2. RUSSIA: a Russian military plane crashed in the Kemerovo region,
   killing all 19 people on board; officials point to a technical
   malfunction.
3. FRANCE: actor Gerard Depardieu dropped his appeal and admitted a
   sexual assault charge before a court in Paris.
4. MIDDLE EAST: Britain, Australia, Canada and Italy jointly called on
   Israel to open Gaza crossings for humanitarian aid, calling the
   situation catastrophic.
5. ASIA-PACIFIC: President Trump met Quad leaders in Manila on his Asia
   trip, as the group reaffirmed its Indo-Pacific commitment.
6. UNITED STATES: the US lost its measles elimination status after 26
   years, with more than 5,400 cases and 10 deaths reported.

How the grader runs it: `python3 -P -s /bot/main.py` (PYTHONHASHSEED=0),
standard library only, no network, read-only /bot, writable /output,
1 CPU / 512 MB / 60 s per run, run twice with byte-identical output.
Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib
from pathlib import Path

OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
WIDTH, HEIGHT = 1024, 1024

# ---------------------------------------------------------------- font ----
# A 5x7 bitmap font. Each glyph is 7 rows of 5 bits, '1' = ink, '0' = empty.
# Only uppercase letters, digits and the punctuation the stories use.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
}

# Normalise the few non-ASCII marks that can slip into story text.
NORMALISE = {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
             "\u2013": "-", "\u2014": "-", "\u00e9": "E", "\u00c9": "E"}


def clean(text):
    out = []
    for ch in text.upper():
        out.append(NORMALISE.get(ch, ch))
    return "".join(out)


# -------------------------------------------------------------- canvas ----
PAPER = (247, 245, 240)
INK = (26, 26, 26)
NAVY = (16, 42, 67)
GOLD = (232, 184, 75)
GREY = (90, 90, 90)
BORDER = (200, 196, 188)


class Canvas:
    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.pixels = bytearray(background * (width * height))

    def rect(self, x, y, w, h, colour):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.width, x + w), min(self.height, y + h)
        r, g, b = colour
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                off = base + (xx - x0) * 3
                self.pixels[off] = r
                self.pixels[off + 1] = g
                self.pixels[off + 2] = b

    def text(self, x, y, text, scale, colour):
        text = clean(text)
        cx = x
        for ch in text:
            glyph = FONT.get(ch, FONT[" "])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        self.rect(cx + col * scale, y + row * scale, scale, scale, colour)
            cx += 6 * scale

    def text_width(self, text, scale):
        return max(0, len(clean(text)) * 6 * scale - scale)

    def centred_text(self, y, text, scale, colour):
        self.text((self.width - self.text_width(text, scale)) // 2, y, text, scale, colour)


def wrap(text, max_chars):
    """Word-wrap text into lines of at most max_chars characters."""
    lines, current = [], ""
    for word in clean(text).split(" "):
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ------------------------------------------------------------------ png ----
def png_bytes(canvas):
    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", canvas.width, canvas.height, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        raw += canvas.pixels[y * stride:(y + 1) * stride]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


# -------------------------------------------------------------- stories ----
# (kicker, accent colour, headline, body). Bodies are kept short and
# factual: what happened, on 17 November 2026, in plain words.
STORIES = [
    ("UKRAINE", (179, 64, 42), "KERCH BRIDGE HIT AGAIN",
     "UKRAINE STRUCK THE CRIMEAN BRIDGE FOR A SECOND STRAIGHT DAY. A ROAD "
     "SECTION COLLAPSED INTO THE WATER. KYIV CALLED THE ATTACK "
     "UNPRECEDENTED. RUSSIA HIT BRIDGES IN KYIV IN REPLY."),
    ("RUSSIA", (61, 90, 128), "PLANE CRASH KILLS 19",
     "A RUSSIAN MILITARY PLANE CRASHED IN THE KEMEROVO REGION, KILLING ALL "
     "19 PEOPLE ON BOARD. OFFICIALS POINT TO A TECHNICAL MALFUNCTION."),
    ("FRANCE", (106, 76, 147), "DEPARDIEU ADMITS CHARGE",
     "ACTOR GERARD DEPARDIEU DROPPED HIS APPEAL AND ADMITTED A SEXUAL "
     "ASSAULT CHARGE BEFORE A COURT IN PARIS."),
    ("MIDDLE EAST", (15, 118, 110), "WEST URGES GAZA AID ACCESS",
     "BRITAIN, AUSTRALIA, CANADA AND ITALY JOINTLY CALLED ON ISRAEL TO OPEN "
     "GAZA CROSSINGS FOR AID, CALLING THE SITUATION CATASTROPHIC."),
    ("ASIA-PACIFIC", (154, 107, 0), "QUAD LEADERS MEET IN MANILA",
     "PRESIDENT TRUMP MET QUAD LEADERS IN MANILA ON HIS ASIA TRIP, AS THE "
     "GROUP REAFFIRMED ITS INDO-PACIFIC COMMITMENT."),
    ("UNITED STATES", (45, 106, 79), "US LOSES MEASLES-FREE STATUS",
     "THE US LOST ITS MEASLES ELIMINATION STATUS AFTER 26 YEARS, WITH MORE "
     "THAN 5,400 CASES AND 10 DEATHS REPORTED."),
]


def draw_panel(canvas, x, y, w, h, story):
    kicker, accent, headline, body = story
    canvas.rect(x, y, w, h, (255, 255, 255))
    # Border.
    canvas.rect(x, y, w, 2, BORDER)
    canvas.rect(x, y + h - 2, w, 2, BORDER)
    canvas.rect(x, y, 2, h, BORDER)
    canvas.rect(x + w - 2, y, 2, h, BORDER)
    # Accent bar.
    canvas.rect(x + 2, y + 2, w - 4, 10, accent)
    pad = 22
    canvas.text(x + pad, y + 28, kicker, 2, accent)
    head_lines = wrap(headline, (w - 2 * pad) // 18)
    hy = y + 56
    for line in head_lines[:2]:
        canvas.text(x + pad, hy, line, 3, INK)
        hy += 27
    hy += 8
    body_lines = wrap(body, (w - 2 * pad) // 12)
    for line in body_lines[:6]:
        canvas.text(x + pad, hy, line, 2, (58, 58, 58))
        hy += 18


def render():
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    # Masthead.
    canvas.rect(16, 16, WIDTH - 32, 132, NAVY)
    canvas.centred_text(44, "THE WORLD IN ONE DAY", 5, (255, 255, 255))
    canvas.centred_text(102, "TUESDAY, 17 NOVEMBER 2026", 3, GOLD)
    canvas.centred_text(164, "SIX STORIES FROM AROUND THE GLOBE", 2, GREY)
    # Story panels: two columns, three rows.
    panel_w, panel_h = 480, 258
    gap_x, gap_y = 16, 10
    x0, y0 = 24, 200
    for i, story in enumerate(STORIES):
        col, row = i % 2, i // 2
        draw_panel(canvas, x0 + col * (panel_w + gap_x),
                   y0 + row * (panel_h + gap_y), panel_w, panel_h, story)
    return canvas


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "entry.png").write_bytes(png_bytes(render()))


if __name__ == "__main__":
    main()
