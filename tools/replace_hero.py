"""Install a full-frame MP4 as the opening hero without re-encoding it.

Run: python tools/replace_hero.py path/to/video.mp4
"""

import argparse
import json
import os
import shutil
import tempfile

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets_src")
MEDIA = os.path.join(ROOT, "public", "media")
MANIFEST = os.path.join(MEDIA, "manifest.json")


def install(source):
    source = os.path.abspath(source)
    if not os.path.isfile(source):
        raise FileNotFoundError("Video not found: %s" % source)
    if os.path.splitext(source)[1].lower() != ".mp4":
        raise ValueError("Full-frame hero source must be an MP4 file")

    cap = cv2.VideoCapture(source)
    ok, frame = cap.read()
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    if not ok or width <= 0 or height <= 0 or frames <= 0 or fps <= 0:
        raise ValueError("Could not read valid video metadata and first frame")

    os.makedirs(SRC, exist_ok=True)
    os.makedirs(MEDIA, exist_ok=True)
    source_copy = os.path.join(SRC, os.path.basename(source))
    hero_path = os.path.join(MEDIA, "hero.mp4")
    poster_path = os.path.join(MEDIA, "hero.jpg")

    if not os.path.exists(source_copy) or not os.path.samefile(source, source_copy):
        shutil.copy2(source, source_copy)
    if not os.path.exists(hero_path) or not os.path.samefile(source, hero_path):
        shutil.copy2(source, hero_path)
    if not cv2.imwrite(poster_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 88]):
        raise OSError("Could not write hero poster: %s" % poster_path)

    with open(MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    hero = manifest.setdefault("clips", {}).setdefault("hero", {})
    hero.update({
        "name": "hero",
        "frames": frames,
        "fps": round(fps, 3),
        "w": width,
        "h": height,
        "mp4": "hero.mp4",
        "poster": "hero.jpg",
        "packed": False,
    })
    hero.pop("webm", None)
    hero.pop("track", None)

    fd, temp_path = tempfile.mkstemp(dir=MEDIA, suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")
        os.replace(temp_path, MANIFEST)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    print("Installed %s (%dx%d, %d frames at %.3f fps)"
          % (os.path.basename(source), width, height, frames, fps))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Full-frame MP4 to install as the hero")
    args = parser.parse_args()
    install(args.video)


if __name__ == "__main__":
    main()
