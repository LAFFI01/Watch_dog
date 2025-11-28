#!/usr/bin/env python3
import cv2
import time
import os
import argparse
from pathlib import Path
from datetime import datetime
import sys

def parse_args():
    p = argparse.ArgumentParser(description="Capture images from webcam with countdown and optional manual capture.")
    p.add_argument("--output", "-o", type=Path, default=Path("captured_images"), help="Output folder")
    p.add_argument("--count", "-n", type=int, default=5, help="Number of images to capture")
    p.add_argument("--delay", "-d", type=int, default=3, help="Delay between automatic captures (seconds)")
    p.add_argument("--camera", "-c", type=int, default=0, help="Camera index (default 0)")
    p.add_argument("--width", type=int, default=640, help="Frame width")
    p.add_argument("--height", type=int, default=480, help="Frame height")
    p.add_argument("--prefix", "-p", type=str, default="image", help="Filename prefix")
    p.add_argument("--manual", "-m", action="store_true", help="Use manual capture (press SPACE to capture, ESC to quit)")
    p.add_argument("--skip-warmup", action="store_true", help="Skip warmup frames")
    return p.parse_args()

def ensure_dir(path: Path):
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"ERROR: Unable to create output directory {path}: {e}")
        sys.exit(1)

def build_filename(folder: Path, prefix: str, idx: int):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(folder / f"{prefix}_{idx:03d}_{ts}.jpg")

def main():
    args = parse_args()
    ensure_dir(args.output)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"ERROR: Cannot open camera index {args.camera}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    # Warm up camera
    if not args.skip_warmup:
        for _ in range(5):
            cap.read()

    print(f"Starting capture: output={args.output}, count={args.count}, delay={args.delay}s, camera={args.camera}")
    img_index = 1
    try:
        while img_index <= args.count:
            ret, frame = cap.read()
            if not ret:
                print("WARNING: Failed to read frame, retrying...")
                time.sleep(0.2)
                continue

            if args.manual:
                cv2.putText(frame, f"Manual capture {img_index}/{args.count} - SPACE to capture, ESC to quit",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.imshow("Webcam", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    print("Quitting by user request.")
                    break
                if key == 32:  # SPACE
                    filename = build_filename(args.output, args.prefix, img_index)
                    cv2.imwrite(filename, frame)
                    print(f"Captured {filename}")
                    img_index += 1
                    # discard a few frames to reduce lag
                    for _ in range(5):
                        cap.read()
                continue

            # Automatic capture with countdown
            start_time = time.time()
            while True:
                elapsed = int(time.time() - start_time)
                remaining = args.delay - elapsed
                display = frame.copy()
                if remaining > 0:
                    text = f"Capturing in {remaining} sec"
                else:
                    text = "Capturing..."
                cv2.putText(display, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                cv2.putText(display, f"{img_index}/{args.count}", (10, args.height - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                cv2.imshow("Webcam", display)

                if remaining <= 0:
                    break

                if cv2.waitKey(100) & 0xFF == ord('q'):
                    print("Quitting by user request.")
                    raise KeyboardInterrupt

                # update frame occasionally to keep preview live
                ret, frame = cap.read()
                if not ret:
                    print("WARNING: Frame dropped during countdown.")
                    time.sleep(0.05)

            # capture final frame
            ret, frame = cap.read()
            if not ret:
                print("WARNING: Failed to grab final frame, skipping this capture.")
            else:
                filename = build_filename(args.output, args.prefix, img_index)
                cv2.imwrite(filename, frame)
                print(f"Captured {filename}")
                img_index += 1

            # discard frames to reduce lag
            for _ in range(5):
                cap.read()

    except KeyboardInterrupt:
        print("Capture interrupted.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Cleanup done.")

if __name__ == "__main__":
    main()
