#!/usr/bin/env python3
"""
remove_watermark.py — removes doctor watermark from dental photos.
Shows interactive editor before each photo.

Keys in editor window:
  ENTER / SPACE — process this photo
  + or =        — add another zone (copy size, offset)
  - or _        — remove selected zone (at least one remains)
  S             — skip this photo
  ESC           — quit all processing
  Click a zone to select it (handles on the active zone only)
"""

import argparse
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np


SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

# Max display width for the combined preview (fits 13" MacBook Air)
MAX_DISPLAY_W = 1100


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default=None)
    parser.add_argument(
        "--region", action="append", nargs=4, type=float,
        metavar=("X1", "Y1", "X2", "Y2"),
        dest="regions",
        help="Normalized rectangle 0..1; pass multiple times for several zones",
    )
    parser.add_argument("--no-skip", action="store_true",
                        help="Overwrite already processed files")
    return parser.parse_args()


def collect_images(input_dir: Path) -> list[Path]:
    return sorted([
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    ])


def _norm_rect_frac(region: list[float], w: int, h: int) -> tuple[int, int, int, int]:
    x1 = int(region[0] * w)
    y1 = int(region[1] * h)
    x2 = int(region[2] * w)
    y2 = int(region[3] * h)
    x1, x2 = max(0, min(w, x1)), max(0, min(w, x2))
    y1, y2 = max(0, min(h, y1)), max(0, min(h, y2))
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    return x1, y1, x2, y2


def build_mask(img: np.ndarray, regions: list[list[float]], threshold: int) -> np.ndarray:
    """Union of smart masks: bright (text) pixels inside each normalized region."""
    h, w = img.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    for region in regions:
        x1, y1, x2, y2 = _norm_rect_frac(region, w, h)
        if x2 <= x1 or y2 <= y1:
            continue
        roi = img[y1:y2, x1:x2]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, bright = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
        bright = cv2.dilate(bright, kernel, iterations=2)
        patch = mask[y1:y2, x1:x2]
        np.maximum(patch, bright, out=patch)

    return mask


def process_image(img: np.ndarray, regions: list[list[float]],
                  threshold: int, radius: int) -> np.ndarray:
    mask = build_mask(img, regions, threshold)
    return cv2.inpaint(img, mask, radius, cv2.INPAINT_TELEA)


def save_image(img: np.ndarray, out_path: Path, orig_path: Path):
    """Сохраняет в том же расширении, что у оригинала; без лишнего сжатия (JPEG max quality, PNG zlib 0, WebP lossless)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = orig_path.suffix.lower()

    if ext in (".jpg", ".jpeg"):
        cv2.imwrite(str(out_path), img, [cv2.IMWRITE_JPEG_QUALITY, 100])
        return

    if ext == ".png":
        cv2.imwrite(str(out_path), img, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        return

    if ext == ".webp":
        if not cv2.imwrite(str(out_path), img, [cv2.IMWRITE_WEBP_QUALITY, 101]):
            cv2.imwrite(str(out_path), img, [cv2.IMWRITE_WEBP_QUALITY, 100])
        return

    if ext == ".gif":
        if cv2.imwrite(str(out_path), img):
            return
        png_path = out_path.with_suffix(".png")
        cv2.imwrite(str(png_path), img, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        print(f"  [!] {orig_path.name}: GIF не удалось записать, сохранено как {png_path.name}")
        return

    cv2.imwrite(str(out_path), img)


HANDLE_R = 5  # corner handle radius in display pixels


def _pixel_rects_to_fractional(
    rects: list[list[int]], w: int, h: int,
) -> list[list[float]]:
    out: list[list[float]] = []
    for rx1, ry1, rx2, ry2 in rects:
        x1, y1, x2, y2 = normalize_pixel_rect(rx1, ry1, rx2, ry2)
        if x2 <= x1 or y2 <= y1:
            continue
        out.append([x1 / w, y1 / h, x2 / w, y2 / h])
    return out


def normalize_pixel_rect(rx1: int, ry1: int, rx2: int, ry2: int) -> tuple[int, int, int, int]:
    x1 = min(rx1, rx2)
    y1 = min(ry1, ry2)
    x2 = max(rx1, rx2)
    y2 = max(ry1, ry2)
    return x1, y1, x2, y2


def draw_editor(
    canvas: np.ndarray,
    img: np.ndarray,
    rects: list[list[int]],
    selected_idx: int,
    thr: int,
    rad: int,
    dw: int,
    dh: int,
    scale: float,
):
    """Render left (editor) + right (result) panels into canvas."""
    h, w = img.shape[:2]
    regions_f = _pixel_rects_to_fractional(rects, w, h)
    norm_rects = [normalize_pixel_rect(*r) for r in rects]

    left_img = img.copy()
    if regions_f:
        mask_full = build_mask(img, regions_f, thr)
        for x1n, y1n, x2n, y2n in norm_rects:
            if x2n <= x1n or y2n <= y1n:
                continue
            overlay = left_img.copy()
            cv2.rectangle(overlay, (x1n, y1n), (x2n, y2n), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.25, left_img, 0.75, 0, left_img)
        blue = left_img.copy()
        blue[mask_full > 0] = (255, 60, 0)
        cv2.addWeighted(blue, 0.55, left_img, 0.45, 0, left_img)

    left_s = cv2.resize(left_img, (dw, dh))

    for i, (x1n, y1n, x2n, y2n) in enumerate(norm_rects):
        if x2n <= x1n or y2n <= y1n:
            continue
        sx1 = int(x1n * scale)
        sy1 = int(y1n * scale)
        sx2 = int(x2n * scale)
        sy2 = int(y2n * scale)
        active = i == selected_idx
        color = (0, 200, 255) if active else (80, 140, 160)
        thick = 2 if active else 1
        cv2.rectangle(left_s, (sx1, sy1), (sx2, sy2), color, thick)
        if active:
            for cx, cy in ((sx1, sy1), (sx2, sy1), (sx1, sy2), (sx2, sy2)):
                cv2.rectangle(
                    left_s,
                    (cx - HANDLE_R, cy - HANDLE_R),
                    (cx + HANDLE_R, cy + HANDLE_R),
                    (255, 255, 255),
                    -1,
                )
                cv2.rectangle(
                    left_s,
                    (cx - HANDLE_R, cy - HANDLE_R),
                    (cx + HANDLE_R, cy + HANDLE_R),
                    (0, 130, 220),
                    2,
                )

    cv2.putText(
        left_s,
        "ORIGINAL  +/= add zone   -/_ remove",
        (8, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 220, 0),
        1,
        cv2.LINE_AA,
    )
    cv2.putText(
        left_s,
        f"thr:{thr}  r:{rad}  zones:{len(regions_f)}",
        (8, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 220, 255),
        1,
        cv2.LINE_AA,
    )

    if regions_f:
        result_img = cv2.inpaint(
            img, build_mask(img, regions_f, thr), rad, cv2.INPAINT_TELEA
        )
    else:
        result_img = img.copy()

    right_s = cv2.resize(result_img, (dw, dh))
    cv2.putText(right_s, "RESULT", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 0), 1, cv2.LINE_AA)

    canvas[:dh, :dw] = left_s
    canvas[:dh, dw : dw * 2] = right_s


def show_editor(
    img: np.ndarray,
    filename: str,
    regions: list[list[float]],
    threshold: int,
    radius: int,
    idx: int,
    total: int,
) -> tuple:
    """
    Interactive editor: several rectangles, top-most hit wins.
    Returns (regions, threshold, radius, action)
    regions: list of [x1,y1,x2,y2] normalized 0..1
    action: 'process' | 'skip' | 'quit'
    """
    h, w = img.shape[:2]

    rects: list[list[int]] = []
    for r in regions:
        x1, y1, x2, y2 = _norm_rect_frac(r, w, h)
        rects.append([x1, y1, x2, y2])
    if not rects:
        x1, y1, x2, y2 = _norm_rect_frac([0.3, 0.4, 0.7, 0.6], w, h)
        rects = [[x1, y1, x2, y2]]

    selected_idx = 0

    scale = min(1.0, MAX_DISPLAY_W / (w * 2))
    dw = max(1, int(w * scale))
    dh = max(1, int(h * scale))

    WIN = (
        f"[{idx}/{total}] {filename}  |  ENTER=OK  +/-=zones  S=Skip  ESC=Quit"
    )
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, dw * 2, dh)

    cv2.createTrackbar("Threshold", WIN, threshold, 255, lambda _v: None)
    cv2.createTrackbar("Radius", WIN, radius, 20, lambda _v: None)

    drag: dict = {
        "active": False,
        "mode": None,
        "ri": None,
        "corner": None,
        "move_start": None,
        "orig": None,
    }

    def hit_corner(mx: float, my: float):
        for ri in range(len(rects) - 1, -1, -1):
            rx1, ry1, rx2, ry2 = normalize_pixel_rect(*rects[ri])
            if rx2 <= rx1 or ry2 <= ry1:
                continue
            corners = [
                (int(rx1 * scale), int(ry1 * scale)),
                (int(rx2 * scale), int(ry1 * scale)),
                (int(rx1 * scale), int(ry2 * scale)),
                (int(rx2 * scale), int(ry2 * scale)),
            ]
            for ci, (cx, cy) in enumerate(corners):
                if abs(mx - cx) <= HANDLE_R + 4 and abs(my - cy) <= HANDLE_R + 4:
                    return ri, ci
        return None

    def hit_inside(mx: float, my: float):
        for ri in range(len(rects) - 1, -1, -1):
            rx1, ry1, rx2, ry2 = normalize_pixel_rect(*rects[ri])
            if rx2 <= rx1 or ry2 <= ry1:
                continue
            sx1 = int(rx1 * scale)
            sy1 = int(ry1 * scale)
            sx2 = int(rx2 * scale)
            sy2 = int(ry2 * scale)
            if sx1 < mx < sx2 and sy1 < my < sy2:
                return ri
        return None

    def add_region():
        nonlocal rects, selected_idx
        rx1, ry1, rx2, ry2 = normalize_pixel_rect(*rects[selected_idx])
        nw, nh = rx2 - rx1, ry2 - ry1
        nw = max(int(0.08 * w), nw)
        nh = max(int(0.06 * h), nh)
        gap = max(2, int(0.02 * w))
        nx1 = rx2 + gap
        if nx1 + nw > w:
            nx1 = max(0, rx1 - nw - gap)
        ny1 = max(0, min(h - nh, ry1))
        nx1 = max(0, min(w - nw, nx1))
        rects.append([nx1, ny1, nx1 + nw, ny1 + nh])
        selected_idx = len(rects) - 1

    def remove_region():
        nonlocal rects, selected_idx
        if len(rects) <= 1:
            return
        del rects[selected_idx]
        selected_idx = min(selected_idx, len(rects) - 1)

    def on_mouse(event, mx, my, flags, _):
        nonlocal selected_idx
        if mx > dw:
            return
        if event == cv2.EVENT_LBUTTONDOWN:
            hc = hit_corner(mx, my)
            if hc is not None:
                ri, ci = hc
                selected_idx = ri
                drag["active"] = True
                drag["mode"] = "corner"
                drag["ri"] = ri
                drag["corner"] = ci
            else:
                hi = hit_inside(mx, my)
                if hi is not None:
                    selected_idx = hi
                    drag["active"] = True
                    drag["mode"] = "move"
                    drag["ri"] = hi
                    drag["move_start"] = (mx, my)
                    drag["orig"] = tuple(rects[hi])
        elif event == cv2.EVENT_MOUSEMOVE and drag["active"]:
            ri = drag["ri"]
            ix = int(mx / scale)
            iy = int(my / scale)
            ix = max(0, min(w, ix))
            iy = max(0, min(h, iy))
            r = rects[ri]
            if drag["mode"] == "corner":
                c = drag["corner"]
                if c == 0:
                    r[0], r[1] = ix, iy
                elif c == 1:
                    r[2], r[1] = ix, iy
                elif c == 2:
                    r[0], r[3] = ix, iy
                else:
                    r[2], r[3] = ix, iy
            else:
                dx = int((mx - drag["move_start"][0]) / scale)
                dy = int((my - drag["move_start"][1]) / scale)
                ox1, oy1, ox2, oy2 = drag["orig"]
                nw = ox2 - ox1
                nh = oy2 - oy1
                nx1 = max(0, min(w - nw, ox1 + dx))
                ny1 = max(0, min(h - nh, oy1 + dy))
                r[0] = nx1
                r[1] = ny1
                r[2] = nx1 + nw
                r[3] = ny1 + nh
        elif event == cv2.EVENT_LBUTTONUP:
            drag["active"] = False
            drag["mode"] = None
            drag["ri"] = None
            drag["corner"] = None

    cv2.setMouseCallback(WIN, on_mouse)

    print(f"\n  [{idx}/{total}] {filename}")
    print("    Click zone to select; drag corners / body.  +/= add zone  -/_ remove")
    print("    ENTER/SPACE = process  |  S = skip  |  ESC = quit all")

    canvas = np.zeros((dh, dw * 2, 3), dtype=np.uint8)
    action = "process"

    while True:
        thr = max(1, cv2.getTrackbarPos("Threshold", WIN))
        rad = max(1, cv2.getTrackbarPos("Radius", WIN))

        draw_editor(canvas, img, rects, selected_idx, thr, rad, dw, dh, scale)
        cv2.imshow(WIN, canvas)

        key = cv2.waitKey(50) & 0xFF
        if key in (13, 32):
            action = "process"
            break
        if key in (ord("s"), ord("S"), ord("n"), ord("N")):
            action = "skip"
            break
        if key == 27:
            action = "quit"
            break
        if key in (ord("+"), ord("=")):
            add_region()
        if key in (ord("-"), ord("_")):
            remove_region()

    cv2.destroyWindow(WIN)

    final_regions: list[list[float]] = []
    for r in rects:
        x1, y1, x2, y2 = normalize_pixel_rect(*r)
        if x2 > x1 and y2 > y1:
            final_regions.append([x1 / w, y1 / h, x2 / w, y2 / h])
    if not final_regions:
        final_regions = [[0.3, 0.4, 0.7, 0.6]]

    return final_regions, thr, rad, action


def main():
    args = parse_args()

    # Folder picker via native macOS dialog
    if not args.input or not Path(args.input).exists():
        script = 'tell app "Finder" to POSIX path of (choose folder with prompt "Select photos folder:")'
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        chosen = res.stdout.strip()
        if not chosen:
            print("Cancelled.")
            sys.exit(0)
        args.input = chosen

    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"[Error] Not a directory: {input_dir}")
        sys.exit(1)

    output_dir = input_dir / "cleaned"
    skip_existing = not args.no_skip

    images = collect_images(input_dir)
    if not images:
        print(f"[!] No images found in: {input_dir}")
        sys.exit(1)

    print(f"\nFolder : {input_dir}")
    print(f"Output : {output_dir}")
    print(f"Found  : {len(images)} images")
    print("\nEditor opens before each photo.")
    print("  ENTER/SPACE = process  |  S = skip  |  ESC = quit all\n")

    # Starting defaults (carry over between photos)
    regions: list[list[float]] = (
        [list(map(float, t)) for t in args.regions]
        if args.regions
        else [[0.3, 0.4, 0.7, 0.6]]
    )
    threshold = 180
    radius = 3

    ok = skipped = failed = 0

    for i, img_path in enumerate(images, 1):
        out_path = output_dir / img_path.name

        if skip_existing and out_path.exists():
            print(f"  [{i}/{len(images)}] Already done, skipping: {img_path.name}")
            skipped += 1
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  [{i}/{len(images)}] Cannot open: {img_path.name}")
            failed += 1
            continue

        # Show editor — settings carry over from previous photo
        regions, threshold, radius, action = show_editor(
            img, img_path.name, regions, threshold, radius, i, len(images)
        )

        if action == "quit":
            print("\nQuitting.")
            break
        elif action == "skip":
            print(f"  [{i}/{len(images)}] Skipped: {img_path.name}")
            skipped += 1
            continue

        # Process and save
        result = process_image(img, regions, threshold, radius)
        save_image(result, out_path, img_path)
        print(f"  [{i}/{len(images)}] Done: {img_path.name}")
        ok += 1

    print(f"\nDone: {ok} processed, {skipped} skipped, {failed} errors")
    print(f"Output: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
