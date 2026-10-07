#!/usr/bin/env python3
"""contrast.py - how readable and how distinguishable are terminal colours?

Usage:
  python3 contrast.py ratio FG BG       WCAG contrast ratio of two colours (#rrggbb)
  python3 contrast.py ls                the colours GNU ls uses, in xterm's default palette:
                                        contrast on black and on white, and how they look
                                        to a viewer with deuteranopia (no green-sensitive cones)
"""
import sys

def srgb_to_linear(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def linear_to_srgb(c):
    c = min(max(c, 0.0), 1.0)
    c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return round(c * 255)

def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def rgb2hex(rgb):
    return "#" + "".join(f"{v:02x}" for v in rgb)

def luminance(rgb):
    r, g, b = (srgb_to_linear(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b     # WCAG relative luminance

def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)                 # 1:1 (none) ... 21:1 (black/white)

# Machado, Oliveira & Fernandes (2009), deuteranomaly at severity 1.0 (= deuteranopia)
DEUTAN = ((0.367322, 0.860646, -0.227968),
          (0.280085, 0.672501, 0.047413),
          (-0.011820, 0.042940, 0.968881))

def deuteranopia(rgb):
    lin = [srgb_to_linear(v) for v in rgb]
    return tuple(linear_to_srgb(sum(m * x for m, x in zip(row, lin))) for row in DEUTAN)

def lab(rgb):                                        # CIE L*a*b* (D65), for colour distance
    r, g, b = (srgb_to_linear(v) for v in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)

def delta_e(a, b):                                   # CIE76 distance; about 2.3 = just noticeable
    return sum((p - q) ** 2 for p, q in zip(lab(a), lab(b))) ** 0.5

# ls uses bold (bright) colours; these are xterm's default bright colours
LS = [("directory (01;34)", "#5c5cff"), ("executable (01;32)", "#00ff00"),
      ("archive (01;31)", "#ff0000"), ("symlink (01;36)", "#00ffff"),
      ("image (01;35)", "#ff00ff")]
BLACK, WHITE = (0, 0, 0), (255, 255, 255)

if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "ratio":
        print(f"contrast {ratio(hex2rgb(sys.argv[2]), hex2rgb(sys.argv[3])):.2f}:1")
    elif sys.argv[1:] == ["ls"]:
        print(f"{'file type (ls code)':20} {'colour':8} {'on black':>9} {'on white':>9}   deuteranopia")
        for name, h in LS:
            c = hex2rgb(h)
            print(f"{name:20} {h:8} {ratio(c, BLACK):8.2f}:1 {ratio(c, WHITE):8.2f}:1   {rgb2hex(deuteranopia(c))}")
        red, green = hex2rgb("#ff0000"), hex2rgb("#00ff00")
        print(f"\ncolour distance archive vs executable (CIE76 delta E):")
        print(f"  normal vision: {delta_e(red, green):6.1f}")
        print(f"  deuteranopia:  {delta_e(deuteranopia(red), deuteranopia(green)):6.1f}")
        dr, dg = lab(deuteranopia(red)), lab(deuteranopia(green))
        print(f"  ...of which lightness (L*): {abs(dr[0] - dg[0]):.1f}  (archive L*={dr[0]:.0f}, executable L*={dg[0]:.0f})")
    else:
        print(__doc__)
