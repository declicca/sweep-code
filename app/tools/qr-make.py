#!/usr/bin/env python3
"""Sweep — the QR code that opens the app on a phone (5 Nov. 2026, brief notifications, step 2): img/qr-app.svg (Settings and
the routine on a computer) and img/qr-app.png (the « Sweep on your phone » email). A small QR encoder (byte mode, error
correction M, versions 1 to 5), after Project Nayuki's reference implementation; no library to install.
    python3 tools/qr-make.py            writes both files for QR_URL
The PNG needs Pillow (~/.venvs/sweep). Development tool only (tools/ is not deployed)."""
import os
import sys

QR_URL = 'https://app.makeitsweep.com/?i=qr'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# error correction M: codewords per block, number of blocks, raw codewords (versions 1 to 5)
ECC_M = {1: 10, 2: 16, 3: 26, 4: 18, 5: 24}
BLOCKS_M = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2}
RAW = {1: 26, 2: 44, 3: 70, 4: 100, 5: 134}
ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30]}


def gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def rs_divisor(degree):
    res = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            res[j] = gf_mul(res[j], root)
            if j + 1 < degree:
                res[j] ^= res[j + 1]
        root = gf_mul(root, 0x02)
    return res


def rs_remainder(data, div):
    res = [0] * len(div)
    for b in data:
        f = b ^ res.pop(0)
        res.append(0)
        for i, c in enumerate(div):
            res[i] ^= gf_mul(c, f)
    return res


def encode(text):
    data = text.encode('utf-8')
    ver = next(v for v in range(1, 6) if 4 + 8 + 8 * len(data) <= (RAW[v] - ECC_M[v] * BLOCKS_M[v]) * 8)
    cap = (RAW[ver] - ECC_M[ver] * BLOCKS_M[ver]) * 8
    bits = [0, 1, 0, 0] + [(len(data) >> i) & 1 for i in reversed(range(8))]
    for b in data:
        bits += [(b >> i) & 1 for i in reversed(range(8))]
    bits += [0] * min(4, cap - len(bits))
    bits += [0] * (-len(bits) % 8)
    pad = 0xEC
    while len(bits) < cap:
        bits += [(pad >> i) & 1 for i in reversed(range(8))]
        pad ^= 0xEC ^ 0x11
    words = [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    # blocks, error correction, interleaving
    nb, ecl, raw = BLOCKS_M[ver], ECC_M[ver], RAW[ver]
    short_n = nb - raw % nb
    short_len = raw // nb
    div = rs_divisor(ecl)
    blocks, k = [], 0
    for i in range(nb):
        dat = words[k:k + short_len - ecl + (0 if i < short_n else 1)]
        k += len(dat)
        ecc = rs_remainder(dat, div)
        if i < short_n:
            dat = dat + [0]
        blocks.append(dat + ecc)
    out = []
    for i in range(len(blocks[0])):
        for j, blk in enumerate(blocks):
            if i != short_len - ecl or j >= short_n:
                out.append(blk[i])
    return ver, out


def matrix(text):
    ver, words = encode(text)
    n = ver * 4 + 17
    mod = [[False] * n for _ in range(n)]
    fn = [[False] * n for _ in range(n)]

    def setf(x, y, dark):
        mod[y][x] = dark
        fn[y][x] = True

    for i in range(n):   # timing
        setf(6, i, i % 2 == 0)
        setf(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):   # finders and separators
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                d = max(abs(dx), abs(dy))
                x, y = cx + dx, cy + dy
                if 0 <= x < n and 0 <= y < n:
                    setf(x, y, d not in (2, 4))
    al = ALIGN[ver]
    for i, a in enumerate(al):
        for j, b in enumerate(al):
            if (i == 0 and j == 0) or (i == 0 and j == len(al) - 1) or (i == len(al) - 1 and j == 0):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    setf(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)

    def format_bits(mask):
        d = (0 << 3) | mask   # error correction M = 0
        r = d
        for _ in range(10):
            r = (r << 1) ^ ((r >> 9) * 0x537)
        b = ((d << 10) | r) ^ 0x5412
        g = lambda i: (b >> i) & 1 == 1
        for i in range(6):
            setf(8, i, g(i))
        setf(8, 7, g(6)); setf(8, 8, g(7)); setf(7, 8, g(8))
        for i in range(9, 15):
            setf(14 - i, 8, g(i))
        for i in range(8):
            setf(n - 1 - i, 8, g(i))
        for i in range(8, 15):
            setf(8, n - 15 + i, g(i))
        setf(8, n - 8, True)

    format_bits(0)   # reserves the format areas
    i, total = 0, len(words) * 8
    right = n - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(n):
            for j in range(2):
                x = right - j
                up = ((right + 1) & 2) == 0
                y = n - 1 - vert if up else vert
                if not fn[y][x] and i < total:
                    mod[y][x] = (words[i >> 3] >> (7 - (i & 7))) & 1 == 1
                    i += 1
        right -= 2

    masks = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
             lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
             lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]

    def apply(m):
        for y in range(n):
            for x in range(n):
                if not fn[y][x] and masks[m](x, y):
                    mod[y][x] = not mod[y][x]

    def penalty():
        p = 0
        for lines in (mod, [list(c) for c in zip(*mod)]):
            for row in lines:
                run = 1
                for k in range(1, n + 1):
                    if k < n and row[k] == row[k - 1]:
                        run += 1
                    else:
                        if run >= 5:
                            p += run - 2
                        run = 1
                s = ''.join('1' if v else '0' for v in row)
                p += 40 * (s.count('10111010000') + s.count('00001011101'))
        for y in range(n - 1):
            for x in range(n - 1):
                if mod[y][x] == mod[y][x + 1] == mod[y + 1][x] == mod[y + 1][x + 1]:
                    p += 3
        dark = sum(v for row in mod for v in row)
        p += 10 * (abs(dark * 20 - n * n * 10) // (n * n))
        return p

    best = None
    for m in range(8):
        apply(m); format_bits(m)
        pen = penalty()
        if best is None or pen < best[0]:
            best = (pen, m)
        apply(m)   # undo (the mask is its own inverse)
    apply(best[1]); format_bits(best[1])
    return mod


def svg(mod, quiet=4):
    n = len(mod) + 2 * quiet
    d = ''.join(f'M{x + quiet} {y + quiet}h1v1h-1z' for y, row in enumerate(mod) for x, v in enumerate(row) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
            f'<rect width="{n}" height="{n}" rx="2" fill="#fff"/><path fill="#08080A" d="{d}"/></svg>\n')


def png(mod, path, scale=8, quiet=4):
    from PIL import Image
    n = (len(mod) + 2 * quiet) * scale
    im = Image.new('L', (n, n), 255)
    px = im.load()
    for y, row in enumerate(mod):
        for x, v in enumerate(row):
            if v:
                for a in range(scale):
                    for b in range(scale):
                        px[(x + quiet) * scale + a, (y + quiet) * scale + b] = 8
    im.save(path, optimize=True)


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else QR_URL
    m = matrix(url)
    with open(os.path.join(ROOT, 'img', 'qr-app.svg'), 'w') as f:
        f.write(svg(m))
    png(m, os.path.join(ROOT, 'img', 'qr-app.png'))
    print(f'{len(m)}×{len(m)} modules: img/qr-app.svg, img/qr-app.png')
