#!/usr/bin/env python3
"""
remove_watermark.py — removes doctor watermark from dental photos.
Shows interactive editor before each photo.

Keys in editor window:
  ENTER / SPACE — process this photo
  S             — skip this photo
  ESC           — quit all processing
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
        "--region", nargs=4, type=float,
        metavar=("X1", "Y1", "X2", "Y2"),
        default=[0.45, 0.88, 1.0, 1.0],
    )
    parser.add_argument("--no-skip", action="store_true",
                        help="Overwrite already processed files")
    return parser.parse_args()


def collect_images(input_dir: Path) -> list[Path]:
    return sorted([
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    ])


def build_mask(img: np.ndarray, region: list[float], threshold: int) -> np.ndarray:
    """Smart mask: only bright (text) pixels inside the region."""
    h, w = img.shape[:2]
    x1 = int(region[0] * w)
    y1 = int(region[1] * h)
    x2 = int(region[2] * w)
    y2 = int(region[3] * h)
    x1, x2 = max(0, x1), min(w, x2)
    y1, y2 = max(0, y1), min(h, y2)

    mask = np.zeros((h, w), dtype=np.uint8)
    if x2 <= x1 or y2 <= y1:
        return mask

    roi = img[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, bright = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    bright = cv2.dilate(bright, kernel, iterations=2)
    mask[y1:y2, x1:x2] = bright
    return mask


def process_image(img: np.ndarray, region: list[float],
                  threshold: int, radius: int) -> np.ndarray:
    mask = build_mask(img, region, threshold)
    return cv2.inpaint(img, mask, radius, cv2.INPAINT_TELEA)


def save_image(img: np.ndarray, out_path: Path, orig_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ext = orig_path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        cv2.imwrite(str(out_path), img, [cv2.IMWRITE_JPEG_QUALITY, 97])
    else:
        cv2.imwrite(str(out_path), img)


HANDLE_R = 5  # corner handle radius in display pixels


def draw_editor(canvas: np.ndarray, img: np.ndarray,
                rx1: int, ry1: int, rx2: int, ry2: int,
                thr: int, rad: int,
                dw: int, dh: int, scale: float):
    """Render left (editor) + right (result) panels into canvas."""
    h, w = img.shape[:2]
    valid = rx2 > rx1 and ry2 > ry1

    # --- LEFT: original + selection box + mask highlight ---
    left_img = img.copy()
    if valid:
        # dim the region
        overlay = left_img.copy()
        cv2.rectangle(overlay, (rx1, ry1), (rx2, ry2), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.25, left_img, 0.75, 0, left_img)

        # highlight detected text pixels (blue)
        region_f = [rx1 / w, ry1 / h, rx2 / w, ry2 / h]
        mask = build_mask(img, region_f, thr)
        blue = left_img.copy()
        blue[mask > 0] = (255, 60, 0)
        cv2.addWeighted(blue, 0.55, left_img, 0.45, 0, left_img)

    left_s = cv2.resize(left_img, (dw, dh))

    if valid:
        # scale coords to display
        sx1 = int(rx1 * scale); sy1 = int(ry1 * scale)
        sx2 = int(rx2 * scale); sy2 = int(ry2 * scale)

        # border
        cv2.rectangle(left_s, (sx1, sy1), (sx2, sy2), (0, 200, 255), 2)

        # 4 corner handles
        for cx, cy in [(sx1, sy1), (sx2, sy1), (sx1, sy2), (sx2, sy2)]:
            cv2.rectangle(left_s,
                          (cx - HANDLE_R, cy - HANDLE_R),
                          (cx + HANDLE_R, cy + HANDLE_R),
                          (255, 255, 255), -1)
            cv2.rectangle(left_s,
                          (cx - HANDLE_R, cy - HANDLE_R),
                          (cx + HANDLE_R, cy + HANDLE_R),
                          (0, 130, 220), 2)

        # info label
        info = f"thr:{thr}  r:{rad}"
        cv2.putText(left_s, info, (sx1, max(sy1 - 6, 14)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1, cv2.LINE_AA)

    cv2.putText(left_s, "ORIGINAL  (drag corners)", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 0), 1, cv2.LINE_AA)

    # --- RIGHT: inpaint result ---
    if valid:
        region_f = [rx1 / w, ry1 / h, rx2 / w, ry2 / h]
        mask = build_mask(img, region_f, thr)
        result_img = cv2.inpaint(img, mask, rad, cv2.INPAINT_TELEA)
    else:
        result_img = img.copy()

    right_s = cv2.resize(result_img, (dw, dh))
    cv2.putText(right_s, "RESULT", (8, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 0), 1, cv2.LINE_AA)

    canvas[:dh, :dw]       = left_s
    canvas[:dh, dw:dw * 2] = right_s


def show_editor(img: np.ndarray, filename: str,
                region: list[float], threshold: int, radius: int,
                idx: int, total: int) -> tuple:
    """
    Interactive editor with draggable corner handles (Figma-style).
    Returns (region, threshold, radius, action)
    action: 'process' | 'skip' | 'quit'
    """
    h, w = img.shape[:2]

    # Scale so both panels fit on screen
    scale = min(1.0, MAX_DISPLAY_W / (w * 2))
    dw = max(1, int(w * scale))
    dh = max(1, int(h * scale))

    WIN = f"[{idx}/{total}] {filename}  |  ENTER=OK  S/N=Skip  ESC=Quit"
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, dw * 2, dh)

    # Trackbars only for Threshold and Radius (region is mouse-driven)
    cv2.createTrackbar("Threshold", WIN, threshold, 255, lambda v: None)
    cv2.createTrackbar("Radius",    WIN, radius,    20,  lambda v: None)

    # Current rectangle in IMAGE pixels
    rx1 = int(region[0] * w); ry1 = int(region[1] * h)
    rx2 = int(region[2] * w); ry2 = int(region[3] * h)

    # Mouse state
    drag = {"active": False, "corner": None, "move_start": None, "orig": None}

    def hit_corner(mx, my):
        """Return corner index (0=TL,1=TR,2=BL,3=BR) if mouse is near it, else None."""
        corners = [
            (int(rx1 * scale), int(ry1 * scale)),
            (int(rx2 * scale), int(ry1 * scale)),
            (int(rx1 * scale), int(ry2 * scale)),
            (int(rx2 * scale), int(ry2 * scale)),
        ]
        for i, (cx, cy) in enumerate(corners):
            if abs(mx - cx) <= HANDLE_R + 4 and abs(my - cy) <= HANDLE_R + 4:
                return i
        return None

    def inside_rect(mx, my):
        sx1 = int(rx1 * scale); sy1 = int(ry1 * scale)
        sx2 = int(rx2 * scale); sy2 = int(ry2 * scale)
        return sx1 < mx < sx2 and sy1 < my < sy2

    def on_mouse(event, mx, my, flags, _):
        nonlocal rx1, ry1, rx2, ry2
        # Mouse operates only on left panel
        if mx > dw:
            return
        if event == cv2.EVENT_LBUTTONDOWN:
            c = hit_corner(mx, my)
            if c is not None:
                drag["active"] = True
                drag["corner"] = c
            elif inside_rect(mx, my):
                drag["active"] = True
                drag["corner"] = "move"
                drag["move_start"] = (mx, my)
                drag["orig"] = (rx1, ry1, rx2, ry2)
        elif event == cv2.EVENT_MOUSEMOVE and drag["active"]:
            ix = int(mx / scale); iy = int(my / scale)
            ix = max(0, min(w, ix)); iy = max(0, min(h, iy))
            c = drag["corner"]
            if c == 0:   rx1, ry1 = ix, iy          # TL
            elif c == 1: rx2, ry1 = ix, iy           # TR
            elif c == 2: rx1, ry2 = ix, iy           # BL
            elif c == 3: rx2, ry2 = ix, iy           # BR
            elif c == "move":
                dx = int((mx - drag["move_start"][0]) / scale)
                dy = int((my - drag["move_start"][1]) / scale)
                ox1, oy1, ox2, oy2 = drag["orig"]
                nw = ox2 - ox1; nh = oy2 - oy1
                nx1 = max(0, min(w - nw, ox1 + dx))
                ny1 = max(0, min(h - nh, oy1 + dy))
                rx1, ry1, rx2, ry2 = nx1, ny1, nx1 + nw, ny1 + nh
        elif event == cv2.EVENT_LBUTTONUP:
            drag["active"] = False
            drag["corner"] = None

    cv2.setMouseCallback(WIN, on_mouse)

    print(f"\n  [{idx}/{total}] {filename}")
    print("    Drag corners or move the box with mouse")
    print("    ENTER/SPACE = process  |  S = skip  |  ESC = quit all")

    canvas = np.zeros((dh, dw * 2, 3), dtype=np.uint8)
    action = "process"

    while True:
        thr = max(1, cv2.getTrackbarPos("Threshold", WIN))
        rad = max(1, cv2.getTrackbarPos("Radius",    WIN))

        # Normalize so x1<x2, y1<y2
        x1n = min(rx1, rx2); x2n = max(rx1, rx2)
        y1n = min(ry1, ry2); y2n = max(ry1, ry2)

        draw_editor(canvas, img, x1n, y1n, x2n, y2n, thr, rad, dw, dh, scale)
        cv2.imshow(WIN, canvas)

        key = cv2.waitKey(50) & 0xFF
        if key in (13, 32):
            action = "process"
            rx1, ry1, rx2, ry2 = x1n, y1n, x2n, y2n
            break
        elif key in (ord('s'), ord('S'), ord('n'), ord('N')):
            action = "skip"
            break
        elif key == 27:
            action = "quit"
            break

    cv2.destroyWindow(WIN)
    final_region = [rx1 / w, ry1 / h, rx2 / w, ry2 / h]
    return final_region, thr, rad, action


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
    region    = args.region[:]
    threshold = 180
    radius    = 3

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
        region, threshold, radius, action = show_editor(
            img, img_path.name, region, threshold, radius, i, len(images)
        )

        if action == "quit":
            print("\nQuitting.")
            break
        elif action == "skip":
            print(f"  [{i}/{len(images)}] Skipped: {img_path.name}")
            skipped += 1
            continue

        # Process and save
        result = process_image(img, region, threshold, radius)
        save_image(result, out_path, img_path)
        print(f"  [{i}/{len(images)}] Done: {img_path.name}")
        ok += 1

    print(f"\nDone: {ok} processed, {skipped} skipped, {failed} errors")
    print(f"Output: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
