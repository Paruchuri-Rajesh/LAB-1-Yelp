"""
============================================================
Load Yelp Reviews into MySQL
============================================================

Run AFTER yelp_scraper.py (businesses must exist first).

Usage:
    python yelp_load_reviews.py

Requirements:
    pip install mysql-connector-python
============================================================
"""

import json
import logging
import mysql.connector
from pathlib import Path

# ── CONFIG (same as yelp_scraper.py) ────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",           # Your MySQL username
    "password": "admin",  # Your MySQL password
    "database": "yelp_db",
    "charset":  "utf8mb4",
}

REVIEWS_FILE = "yelp_reviews.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ── Ensure reviews table exists ──────────────────────────────
CREATE_REVIEWS_TABLE = """
CREATE TABLE IF NOT EXISTS reviews (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    business_id     INT             NOT NULL,
    author          VARCHAR(255),
    rating          DECIMAL(2,1),
    review_text     TEXT,
    review_date     DATE,
    useful_votes    INT             DEFAULT 0,
    funny_votes     INT             DEFAULT 0,
    cool_votes      INT             DEFAULT 0,
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    INDEX idx_business_id  (business_id),
    INDEX idx_rating       (rating),
    INDEX idx_review_date  (review_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

INSERT_REVIEW_SQL = """
    INSERT INTO reviews
        (business_id, author, rating, review_text, review_date,
         useful_votes, funny_votes, cool_votes, created_at)
    VALUES
        (%(business_id)s, %(author)s, %(rating)s, %(review_text)s,
         %(review_date)s, %(useful_votes)s, %(funny_votes)s,
         %(cool_votes)s, %(created_at)s)
"""


def load_reviews(conn, reviews: list[dict]) -> int:
    cursor = conn.cursor()
    # Create table if missing
    cursor.execute(CREATE_REVIEWS_TABLE)
    conn.commit()
    log.info("Reviews table ready.")

    inserted = 0
    for rev in reviews:
        # Strip non-DB fields
        row = {k: rev[k] for k in (
            "business_id", "author", "rating", "review_text", "review_date",
            "useful_votes", "funny_votes", "cool_votes", "created_at"
        )}
        try:
            cursor.execute(INSERT_REVIEW_SQL, row)
            inserted += 1
        except mysql.connector.Error as e:
            log.warning(f"Skipping review id={rev.get('id')}: {e}")

    conn.commit()
    cursor.close()
    log.info(f"Inserted {inserted}/{len(reviews)} reviews.")
    return inserted


def main():
    # Load JSON
    path = Path(REVIEWS_FILE)
    if not path.exists():
        log.error(f"File not found: {REVIEWS_FILE}")
        return
    with open(path, "r", encoding="utf-8") as f:
        reviews = json.load(f)
    log.info(f"Loaded {len(reviews)} reviews from {REVIEWS_FILE}")

    # Connect
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        log.info("Connected to MySQL.")
    except mysql.connector.Error as e:
        log.error(f"Cannot connect to MySQL: {e}")
        return

    inserted = load_reviews(conn, reviews)
    conn.close()

    log.info(f"Done! {inserted} reviews now in MySQL table 'reviews'.")
    log.info("Verify:  SELECT b.name, COUNT(r.id) AS reviews, AVG(r.rating) AS avg")
    log.info("         FROM businesses b JOIN reviews r ON b.id = r.business_id")
    log.info("         GROUP BY b.id ORDER BY reviews DESC LIMIT 10;")


if __name__ == "__main__":
    main()
