#!/usr/bin/env python3
"""Procedural steaming ramen bowl — pure Pillow, deterministic."""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
rng = random.Random(20261122)

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def radial_gradient(size, center, r0, r1, c_inner, c_outer):
    img = Image.new("RGB", (size, size), c_outer)
    px = img.load()
    cx, cy = center
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - cx, y - cy)
            t = max(0.0, min(1.0, (d - r0) / max(1.0, (r1 - r0))))
            px[x, y] = lerp(c_inner, c_outer, t)
    return img

def add_noise(img, amount=6):
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            n = rng.randint(-amount, amount)
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img

def draw_table(img):
    d = ImageDraw.Draw(img)
    # dark wood base
    d.rectangle([0, 0, W, H], fill=(38, 26, 18))
    # planks horizontal
    plank_h = 128
    for i in range(0, H, plank_h):
        shade = rng.randint(-8, 8)
        d.rectangle([0, i, W, i + plank_h - 2], fill=(46 + shade, 32 + shade // 2, 20 + shade // 3))
        d.line([0, i + plank_h - 2, W, i + plank_h - 2], fill=(18, 12, 8), width=3)
        # grain lines
        for _ in range(14):
            gy = i + rng.randint(6, plank_h - 10)
            d.line([0, gy, W, gy + rng.randint(-4, 4)], fill=(56 + shade, 40, 26), width=1)
    # vignette darkening edges
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-220, -220, W + 220, H + 220], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    black = Image.new("RGB", (W, H), (10, 6, 4))
    img.paste(Image.composite(img, black, vig), (0, 0))
    return img

def draw_bowl(img):
    cx, cy = 512, 520
    # soft shadow
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([cx - 430, cy - 400, cx + 430, cy + 440], fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img)
    R = 408
    # outer ceramic rim
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(24, 24, 28))
    d.ellipse([cx - R + 6, cy - R + 6, cx + R - 6, cy + R - 6], fill=(52, 52, 58))
    # rim highlight arc top-left
    d.arc([cx - R + 10, cy - R + 10, cx + R - 10, cy + R - 10], start=150, end=320, fill=(120, 120, 128), width=5)
    # inner broth area
    Ri = R - 34
    broth = radial_gradient(W, (cx - 60, cy - 70), 40, Ri, (232, 150, 58), (122, 58, 18))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx - Ri, cy - Ri, cx + Ri, cy + Ri], fill=255)
    img.paste(broth, (0, 0), mask)
    return cx, cy, Ri

def draw_noodles(img, cx, cy, Ri):
    d = ImageDraw.Draw(img, "RGBA")
    # clip helper: only draw points inside broth circle
    def inside(x, y):
        return math.hypot(x - cx, y - cy) < Ri - 8
    # many overlapping sine strands, lower half + center swirl
    for k in range(55):
        base_y = cy - Ri * 0.55 + (k / 55.0) * Ri * 1.35
        amp = rng.uniform(8, 26)
        freq = rng.uniform(0.012, 0.03)
        phase = rng.uniform(0, math.tau)
        x0 = cx - Ri + 20
        x1 = cx + Ri - 20
        pts = []
        pts_shadow = []
        for x in range(int(x0), int(x1), 6):
            y = base_y + amp * math.sin(freq * x + phase) + rng.uniform(-1.5, 1.5)
            if inside(x, y):
                pts.append((x, y))
                pts_shadow.append((x + 2, y + 3))
        if len(pts) > 3:
            d.line(pts_shadow, fill=(150, 95, 30, 160), width=7)
            d.line(pts, fill=(248, 220, 138, 255), width=6)
    # central swirl: concentric wavy rings
    for ring in range(7):
        rr = 40 + ring * 34
        pts = []
        for a in range(0, 360, 4):
            rad = math.radians(a)
            wob = 10 * math.sin(rad * 5 + ring)
            x = cx - 30 + (rr + wob) * math.cos(rad)
            y = cy + 30 + (rr + wob) * 0.92 * math.sin(rad)
            if inside(x, y):
                pts.append((x, y))
        if len(pts) > 5:
            d.line(pts + [pts[0]], fill=(250, 226, 150, 255), width=5)
    return img

def draw_chili_oil(img, cx, cy, Ri):
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(26):
        ang = rng.uniform(0, math.tau)
        dist = rng.uniform(40, Ri - 60)
        x = cx + dist * math.cos(ang)
        y = cy + dist * math.sin(ang)
        r = rng.uniform(10, 34)
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=(205, 62, 18, 150))
        d.ellipse([x - r * 0.4, y - r * 0.25, x + r * 0.15, y + r * 0.05], fill=(255, 190, 110, 200))
    # big soft broth gloss (top-left light)
    gloss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    gd.ellipse([cx - 300, cy - 320, cx - 20, cy - 120], fill=(255, 240, 200, 90))
    gloss = gloss.filter(ImageFilter.GaussianBlur(40))
    img.paste(Image.alpha_composite(img.convert("RGBA"), gloss).convert("RGB"), (0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    # gloss streaks
    for _ in range(10):
        x = cx + rng.uniform(-Ri * 0.6, Ri * 0.6)
        y = cy + rng.uniform(-Ri * 0.6, Ri * 0.6)
        if math.hypot(x - cx, y - cy) < Ri - 40:
            d.line([x, y, x + rng.uniform(30, 90), y + rng.uniform(-8, 8)], fill=(255, 235, 190, 130), width=6)
    return img

def draw_egg(img, ex, ey, angle_deg):
    # halved soft egg: white + glossy orange yolk
    egg = Image.new("RGBA", (220, 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(egg)
    d.ellipse([8, 8, 212, 172], fill=(250, 246, 236, 255))
    d.ellipse([16, 14, 204, 164], fill=(255, 252, 244, 255))
    # yolk (jammy: deep orange center)
    d.ellipse([62, 38, 162, 142], fill=(245, 118, 12, 255))
    d.ellipse([74, 48, 150, 130], fill=(255, 140, 26, 255))
    d.ellipse([92, 66, 132, 112], fill=(232, 96, 8, 255))
    # gloss highlight
    d.ellipse([86, 56, 118, 82], fill=(255, 226, 170, 230))
    d.ellipse([94, 60, 110, 72], fill=(255, 250, 230, 255))
    egg = egg.rotate(angle_deg, expand=True, resample=Image.BICUBIC)
    img.paste(egg, (int(ex - egg.width / 2), int(ey - egg.height / 2)), egg)
    return img

def draw_chashu(img, ex, ey, angle_deg):
    s = Image.new("RGBA", (200, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.ellipse([4, 4, 196, 146], fill=(146, 84, 52, 255))
    d.ellipse([16, 14, 184, 136], fill=(186, 118, 78, 255))
    d.ellipse([52, 38, 148, 112], fill=(214, 156, 110, 255))
    d.ellipse([78, 58, 122, 94], fill=(236, 196, 150, 255))
    d.arc([20, 18, 180, 132], start=200, end=330, fill=(255, 220, 180, 180), width=4)
    s = s.rotate(angle_deg, expand=True, resample=Image.BICUBIC)
    img.paste(s, (int(ex - s.width / 2), int(ey - s.height / 2)), s)
    return img

def draw_toppings(img, cx, cy, Ri):
    d = ImageDraw.Draw(img, "RGBA")
    # nori sheets (dark rectangles, top area)
    for (nx, ny, ang) in [(cx - 250, cy - 250, -18), (cx - 170, cy - 285, 10)]:
        nori = Image.new("RGBA", (150, 120), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nori)
        nd.rectangle([2, 2, 148, 118], fill=(16, 26, 18, 255))
        nd.rectangle([8, 8, 142, 112], fill=(22, 38, 24, 255))
        nori = nori.rotate(ang, expand=True, resample=Image.BICUBIC)
        img.paste(nori, (int(nx - nori.width / 2), int(ny - nori.height / 2)), nori)
    d = ImageDraw.Draw(img, "RGBA")
    # scallions: small green rings scattered
    for _ in range(70):
        ang = rng.uniform(0, math.tau)
        dist = rng.uniform(20, Ri - 50)
        x = cx + dist * math.cos(ang)
        y = cy + dist * math.sin(ang)
        r = rng.uniform(5, 10)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(46, 160, 60, 255), width=3)
        d.ellipse([x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4], fill=(140, 220, 130, 200))
    # sesame
    for _ in range(60):
        ang = rng.uniform(0, math.tau)
        dist = rng.uniform(10, Ri - 40)
        x = cx + dist * math.cos(ang)
        y = cy + dist * math.sin(ang)
        d.ellipse([x - 3, y - 2, x + 3, y + 2], fill=(252, 246, 220, 255))
    return img

def draw_chopsticks(img):
    # resting diagonally top-right, over bowl edge
    sticks = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(sticks)
    for off in (0, 22):
        d.line([(700 + off, 60), (560 + off, 430)], fill=(96, 58, 30, 255), width=11)
        d.line([(702 + off, 60), (562 + off, 430)], fill=(150, 100, 55, 255), width=4)
    img.paste(Image.alpha_composite(img.convert("RGBA"), sticks).convert("RGB"), (0, 0))
    return img

def draw_steam(img):
    steam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(steam)
    for sx in (380, 470, 560, 640):
        pts = []
        for t in range(0, 260, 8):
            x = sx + 34 * math.sin(t * 0.045 + sx)
            y = 300 - t
            pts.append((x, y))
        d.line(pts, fill=(255, 255, 255, 210), width=30)
    steam = steam.filter(ImageFilter.GaussianBlur(14))
    # fade steam toward top
    fade = Image.new("L", (W, H), 0)
    fd = ImageDraw.Draw(fade)
    for y in range(H):
        a = max(0, min(255, int(255 * (1 - max(0, 320 - y) / 320.0)))) if y < 320 else 255
        fd.line([0, y, W, y], fill=a)
    steam.putalpha(Image.composite(steam.getchannel("A"), Image.new("L", (W, H), 0), fade))
    img.paste(Image.alpha_composite(img.convert("RGBA"), steam).convert("RGB"), (0, 0))
    return img

def main():
    img = Image.new("RGB", (W, H), (38, 26, 18))
    img = draw_table(img)
    cx, cy, Ri = draw_bowl(img)
    img = draw_noodles(img, cx, cy, Ri)
    img = draw_chili_oil(img, cx, cy, Ri)
    img = draw_toppings(img, cx, cy, Ri)
    img = draw_chashu(img, cx + 190, cy - 120, 24)
    img = draw_chashu(img, cx + 235, cy - 40, -12)
    img = draw_egg(img, cx - 150, cy - 60, -14)
    img = draw_egg(img, cx + 60, cy + 190, 18)
    img = draw_chopsticks(img)
    img = draw_steam(img)
    # gentle overall softness + texture
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    img = add_noise(img, amount=1)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    img.save(out_path, format="PNG", optimize=True)
    print(f"wrote {out_path} {img.size[0]}x{img.size[1]}")

if __name__ == "__main__":
    main()
