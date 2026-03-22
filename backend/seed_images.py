"""Generate colorful restaurant placeholder images locally (no downloads needed)."""
import sys, os, struct, zlib, random, colorsys
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models.restaurant import Restaurant

db = SessionLocal()
restaurants = db.query(Restaurant).all()
upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "restaurants")
os.makedirs(upload_dir, exist_ok=True)

# Color palettes per cuisine type
cuisine_colors = {
    "Italian": [(200, 50, 50), (180, 80, 40), (220, 180, 100)],
    "Chinese": [(200, 40, 40), (220, 160, 40), (180, 30, 30)],
    "Mexican": [(220, 120, 30), (40, 160, 70), (200, 50, 50)],
    "Indian": [(220, 150, 30), (200, 80, 30), (180, 50, 20)],
    "Japanese": [(220, 80, 80), (240, 220, 200), (60, 60, 60)],
    "American": [(60, 80, 160), (200, 50, 50), (240, 220, 180)],
    "Thai": [(80, 180, 80), (220, 180, 40), (200, 60, 60)],
    "French": [(40, 60, 120), (240, 220, 200), (180, 140, 100)],
    "Korean": [(200, 60, 60), (60, 60, 60), (240, 200, 160)],
    "Mediterranean": [(40, 120, 180), (240, 200, 140), (100, 160, 80)],
}

def create_png(width, height, color1, color2, text):
    """Create a simple PNG with gradient and text overlay effect."""
    raw_data = []
    for y in range(height):
        row = b'\x00'  # filter byte
        t = y / height
        for x in range(width):
            s = x / width
            # Create gradient with some variation
            r = int(color1[0] * (1 - t) + color2[0] * t + 20 * (0.5 - abs(s - 0.5)))
            g = int(color1[1] * (1 - t) + color2[1] * t + 15 * (0.5 - abs(s - 0.5)))
            b = int(color1[2] * (1 - t) + color2[2] * t + 10 * (0.5 - abs(s - 0.5)))

            # Add subtle pattern
            if (x // 40 + y // 40) % 2 == 0:
                r = min(255, r + 8)
                g = min(255, g + 8)
                b = min(255, b + 8)

            # Dark overlay band in middle for text area
            if 0.35 < t < 0.65:
                darken = 0.5 + 0.5 * abs(t - 0.5) / 0.15
                r = int(r * darken)
                g = int(g * darken)
                b = int(b * darken)

            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            row += struct.pack('BBB', r, g, b)
        raw_data.append(row)

    raw = b''.join(raw_data)

    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = make_chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    idat = make_chunk(b'IDAT', zlib.compress(raw))
    iend = make_chunk(b'IEND', b'')

    return header + ihdr + idat + iend

count = 0
for restaurant in restaurants:
    filename = f"restaurant_{restaurant.id}.jpg"
    # Use .png since we generate PNGs
    filename = f"restaurant_{restaurant.id}.png"
    filepath = os.path.join(upload_dir, filename)

    colors = cuisine_colors.get(restaurant.cuisine_type, [(100, 100, 100), (60, 60, 60), (140, 140, 140)])
    c1, c2 = random.sample(colors, 2)

    png_data = create_png(800, 500, c1, c2, restaurant.name)
    with open(filepath, 'wb') as f:
        f.write(png_data)

    restaurant.photos = [f"/uploads/restaurants/{filename}"]
    count += 1
    print(f"Created image for: {restaurant.name}")

db.commit()
print(f"\nDone! Created images for {count} restaurants.")
db.close()
