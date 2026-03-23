"""
Force-localize all remote `restaurant_photos.file_path` entries by creating
SVG placeholder files and updating the DB to point at the local `/uploads/...` paths.

Run from the `backend/` folder:
    python -m seeds.force_localize_photos

This is a last-resort fix when remote downloads fail or S3 links are inaccessible.
"""
import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.restaurant import RestaurantPhoto, Restaurant
from app.config import settings


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def esc(s: str) -> str:
    return (
        s.replace('&', '&amp;')
         .replace('<', '&lt;')
         .replace('>', '&gt;')
         .replace('"', '&quot;')
         .replace("'", '&apos;')
    )


def make_svg(path: Path, text: str) -> str:
    w, h = 800, 600
    words = (text or "Restaurant").split()
    lines = []
    line = ""
    for w2 in words:
        if len(line + " " + w2) > 20:
            lines.append(line.strip())
            line = w2
        else:
            line = (line + " " + w2).strip()
    if line:
        lines.append(line)

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


def run(dry: bool = False):
    upload_dir = Path(settings.UPLOAD_DIR)
    target_dir = upload_dir / "restaurant_photos"
    ensure_dir(target_dir)

    db = SessionLocal()
    try:
        photos = db.query(RestaurantPhoto).all()
        updated = 0
        processed = 0
        for p in photos:
            processed += 1
            src = p.file_path or ""
            if not src.lower().startswith('http'):
                continue
            filename_base = f"{p.restaurant_id}_{p.id}_forced"
            temp_path = target_dir / filename_base
            rest = db.query(Restaurant).filter(Restaurant.id == p.restaurant_id).first()
            label = (rest.name if rest else f"Restaurant {p.restaurant_id}")
            if dry:
                print(f"[dry] would create placeholder for photo {p.id} -> {temp_path}.svg")
                updated += 1
                continue
            fname = make_svg(temp_path, label)
            local_url = f"/uploads/restaurant_photos/{fname}"
            p.file_path = local_url
            db.add(p)
            # if primary, update businesses.image_url
            if getattr(p, 'is_primary', False):
                try:
                    rest = db.query(Restaurant).filter(Restaurant.id == p.restaurant_id).first()
                    if rest:
                        rest.image_url = local_url
                        db.add(rest)
                except Exception:
                    pass
            updated += 1
            if updated % 50 == 0:
                db.commit()
        db.commit()
        print(f"Processed {processed} photos, updated {updated} file paths to local placeholders.")
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run(dry=args.dry_run)
