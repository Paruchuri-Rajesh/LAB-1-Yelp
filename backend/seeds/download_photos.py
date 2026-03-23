"""
Download restaurant photos referenced in `restaurant_photos.file_path` and
save them into the project's `uploads/restaurant_photos/` directory. The script
will update the `file_path` column to point to the local `/uploads/...` URL
so the frontend can load images served by the backend's static mount.

Usage (from `backend/`):
    python -m seeds.download_photos
    python -m seeds.download_photos --dry-run      # don't write or update DB
    python -m seeds.download_photos --force         # re-download even if local

Notes:
 - Relies on `requests` (already in requirements.txt).
 - Saves files under `<UPLOAD_DIR>/restaurant_photos/` and updates DB to
   `/uploads/restaurant_photos/<filename>` which matches the backend static mount.
"""
import sys
from pathlib import Path
import os
import shutil
import argparse
import mimetypes

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from app.database import SessionLocal
from app.models.restaurant import RestaurantPhoto, Restaurant
from app.config import settings
import io


def generate_placeholder_image(path: Path, text: str) -> str:
    """Generate a simple SVG placeholder with centered text and save to path.
    Returns the generated filename (not full path).
    """
    try:
        w, h = 800, 600
        # escape text for XML
        def esc(s: str) -> str:
            return (
                s.replace('&', '&amp;')
                 .replace('<', '&lt;')
                 .replace('>', '&gt;')
                 .replace('"', '&quot;')
                 .replace("'", '&apos;')
            )

        lines = []
        words = (text or "Restaurant").split()
        line = ""
        for w in words:
            if len(line + " " + w) > 20:
                lines.append(line.strip())
                line = w
            else:
                line = (line + " " + w).strip()
        if line:
            lines.append(line)

        # build SVG text lines
        svg_lines = []
        y_start = h/2 - (len(lines)-1)*12
        for i, ln in enumerate(lines):
            y = y_start + i*24
            svg_lines.append(f'<text x="50%" y="{y}" text-anchor="middle" fill="#333" font-size="20" font-family="Arial,Helvetica,sans-serif">{esc(ln)}</text>')

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="#e6e6e6" />
  <g dominant-baseline="middle">
    {''.join(svg_lines)}
  </g>
</svg>
'''
        final = path.with_suffix('.svg')
        with open(final, 'w', encoding='utf-8') as f:
            f.write(svg)
        return final.name
    except Exception as e:
        print(f"Failed to generate placeholder image for {text}: {e}")
        return None


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    # keep alnum, dash, underscore, dot
    return "".join(c for c in name if c.isalnum() or c in "-_.")


def download_url_to(path: Path, url: str, timeout: int = 15):
    try:
        resp = requests.get(url, stream=True, timeout=timeout)
        resp.raise_for_status()
        # determine extension
        content_type = resp.headers.get("content-type", "")
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) if content_type else None
        if not ext:
            # fallback from URL
            parsed = os.path.splitext(url.split("?")[0])
            ext = parsed[1] or ".jpg"
        final_path = path.with_suffix(ext)
        with open(final_path, "wb") as f:
            shutil.copyfileobj(resp.raw, f)
        return True, final_path.name
    except Exception as e:
        # Don't fail hard here; caller can attempt a fallback (e.g., Unsplash)
        print(f"Failed to download {url}: {e}")
        return False, None


def run(dry_run: bool = False, force: bool = False):
    upload_dir = Path(settings.UPLOAD_DIR)
    target_dir = upload_dir / "restaurant_photos"
    ensure_dir(target_dir)

    db = SessionLocal()
    try:
        photos = db.query(RestaurantPhoto).all()
        total = len(photos)
        # If there are no RestaurantPhoto rows, seed them from the businesses.image_url
        if total == 0:
            print("No restaurant_photos found — creating from businesses.image_url ...")
            restaurants = db.query(Restaurant).all()
            for r in restaurants:
                img = getattr(r, "image_url", None) or getattr(r, "yelp_url", None)
                if not img:
                    continue
                photo = RestaurantPhoto(
                    restaurant_id=r.id,
                    file_path=img,
                    caption=None,
                    is_primary=True,
                )
                db.add(photo)
            db.commit()
            photos = db.query(RestaurantPhoto).all()
            total = len(photos)
        downloaded = 0
        skipped = 0
        updated = 0

        for idx, p in enumerate(photos, start=1):
            src = p.file_path or ""
            # skip already-local paths
            if src.startswith("/uploads/") and not force:
                # ensure businesses.image_url points to this local path
                try:
                    rest = db.query(Restaurant).filter(Restaurant.id == p.restaurant_id).first()
                    if rest and (not getattr(rest, "image_url", None)):
                        rest.image_url = src
                        db.add(rest)
                except Exception:
                    pass
                skipped += 1
                continue

            if not src.lower().startswith("http"):
                skipped += 1
                continue

            filename_base = sanitize_filename(f"{p.restaurant_id}_{p.id}")
            # temp path without ext; download function will pick ext
            temp_path = target_dir / filename_base

            if dry_run:
                print(f"[dry] would download {src} -> {temp_path}")
                downloaded += 1
                continue

            ok, saved_name = download_url_to(temp_path, src)
            if not ok:
                # Attempt Unsplash fallback using restaurant info
                try:
                    rest = db.query(Restaurant).filter(Restaurant.id == p.restaurant_id).first()
                    query = (rest.cuisine_type or rest.name or "food").split(",")[0]
                    fallback_url = f"https://source.unsplash.com/800x600/?{query},restaurant,food&sig={os.urandom(2).hex()}"
                    print(f"Falling back to Unsplash for restaurant {p.restaurant_id}: {fallback_url}")
                    ok, saved_name = download_url_to(temp_path, fallback_url)
                except Exception as e:
                    print(f"Fallback failed for {p.restaurant_id}: {e}")
                    ok = False

            if not ok:
                # As a final fallback, generate a local placeholder image with the restaurant name
                try:
                    rest = db.query(Restaurant).filter(Restaurant.id == p.restaurant_id).first()
                    label = (rest.name or rest.cuisine_type or f"Restaurant {p.restaurant_id}")
                    print(f"Generating placeholder for restaurant {p.restaurant_id}: {label}")
                    gen_name = generate_placeholder_image(temp_path, label)
                    if gen_name:
                        ok = True
                        saved_name = gen_name
                except Exception as e:
                    print(f"Placeholder generation failed for {p.restaurant_id}: {e}")
                    ok = False

            if not ok:
                continue

            local_url = f"/uploads/restaurant_photos/{saved_name}"
            p.file_path = local_url
            db.add(p)
            # If this photo is primary, update the businesses.image_url to the local path
            try:
                if getattr(p, "is_primary", False):
                    rest = db.query(Restaurant).filter(Restaurant.id == p.restaurant_id).first()
                    if rest:
                        rest.image_url = local_url
                        db.add(rest)
            except Exception:
                pass
            updated += 1
            downloaded += 1

            if idx % 50 == 0:
                db.commit()
                print(f"Processed {idx}/{total} — downloaded {downloaded}, updated {updated}")

        db.commit()
        print(f"Done — processed {total}. downloaded: {downloaded}, updated: {updated}, skipped: {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Re-download even if local path already set")
    args = parser.parse_args()
    run(dry_run=args.dry_run, force=args.force)
