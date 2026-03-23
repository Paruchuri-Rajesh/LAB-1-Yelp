"""
============================================================
Yelp Business Scraper — Full Pipeline
============================================================

SETUP:
    pip install requests beautifulsoup4 mysql-connector-python selenium webdriver-manager

USAGE:
    1. Update DB_CONFIG with your MySQL credentials
    2. Run: python yelp_scraper.py

NOTE:
    Yelp actively blocks automated requests (DataDome CAPTCHA).
    This script uses:
      - Option A: Yelp Fusion API (official, recommended)
      - Option B: Browser-based scraping with Selenium (fallback)
      - Option C: Load from pre-scraped JSON file (included)
============================================================
"""

import json
import time
import random
import logging
import requests
import mysql.connector
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

DB_CONFIG = {
    "host":     "localhost",      # Change if needed
    "port":     3306,
    "user":     "root",           # Your MySQL username
    "password": "admin",  # Your MySQL password
    "database": "yelp_db",
    "charset":  "utf8mb4",
}

YELP_API_KEY = "YOUR_YELP_FUSION_API_KEY"   # Get free at https://www.yelp.com/developers

SEARCH_PARAMS = {
    "term":     "restaurants",
    "location": "New York, NY",
    "limit":    50,       # Max 50 per request
    "offset":   0,
    "sort_by":  "rating",
}

DATA_FILE = "yelp_businesses.json"   # Pre-scraped fallback data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# OPTION A: Yelp Fusion API (Official)
# ─────────────────────────────────────────────

def fetch_via_api(api_key: str, params: dict) -> list[dict]:
    """
    Fetch businesses using official Yelp Fusion API.
    Free tier: 500 calls/day, 50 results per call.
    Get your API key: https://www.yelp.com/developers/v3/manage_app
    """
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    businesses = []

    while True:
        log.info(f"Fetching offset {params['offset']} ...")
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("businesses", [])
        if not batch:
            break

        for b in batch:
            loc = b.get("location", {})
            coord = b.get("coordinates", {})
            businesses.append({
                "yelp_id":      b.get("id", ""),
                "name":         b.get("name", ""),
                "alias":        b.get("alias", ""),
                "category":     ", ".join(c["title"] for c in b.get("categories", [])),
                "rating":       b.get("rating", 0),
                "review_count": b.get("review_count", 0),
                "price_range":  b.get("price", ""),
                "phone":        b.get("phone", ""),
                "address":      loc.get("address1", ""),
                "city":         loc.get("city", ""),
                "state":        loc.get("state", ""),
                "zip_code":     loc.get("zip_code", ""),
                "country":      loc.get("country", "US"),
                "latitude":     coord.get("latitude"),
                "longitude":    coord.get("longitude"),
                "is_closed":    b.get("is_closed", False),
                "website":      b.get("url", ""),
                "hours":        json.dumps({}),
                "image_url":    b.get("image_url", ""),
                "yelp_url":     b.get("url", ""),
                "transactions": ", ".join(b.get("transactions", [])),
                "created_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

        params["offset"] += len(batch)
        total = data.get("total", 0)
        log.info(f"  Got {len(businesses)}/{total} businesses")

        if params["offset"] >= min(total, 1000):   # Yelp caps at 1000
            break

        time.sleep(0.5)   # Rate limiting

    return businesses


# ─────────────────────────────────────────────
# OPTION B: Browser Scraping (Selenium)
# ─────────────────────────────────────────────

def fetch_via_selenium(search_term: str, location: str, max_pages: int = 5) -> list[dict]:
    """
    Scrape Yelp search results using Selenium with stealth settings.
    Install: pip install selenium webdriver-manager
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        import json as _json
    except ImportError:
        log.error("Selenium not installed. Run: pip install selenium webdriver-manager")
        return []

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    businesses = []
    try:
        for page in range(max_pages):
            offset = page * 10
            url = (
                f"https://www.yelp.com/search"
                f"?find_desc={requests.utils.quote(search_term)}"
                f"&find_loc={requests.utils.quote(location)}"
                f"&start={offset}"
            )
            log.info(f"Scraping page {page+1}: {url}")
            driver.get(url)
            time.sleep(random.uniform(3, 6))

            # Check for block
            if "You have been blocked" in driver.page_source:
                log.warning("Yelp blocked the request. Try adding a proxy.")
                break

            # Extract JSON-LD data
            scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            for s in scripts:
                try:
                    data = _json.loads(s.get_attribute("innerHTML"))
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if item.get("@type") in ("Restaurant", "LocalBusiness", "FoodEstablishment"):
                            addr = item.get("address", {})
                            agg  = item.get("aggregateRating", {})
                            businesses.append({
                                "yelp_id":      item.get("url", "").split("/biz/")[-1],
                                "name":         item.get("name", ""),
                                "alias":        item.get("url", "").split("/biz/")[-1],
                                "category":     item.get("servesCuisine", ""),
                                "rating":       agg.get("ratingValue", 0),
                                "review_count": agg.get("reviewCount", 0),
                                "price_range":  item.get("priceRange", ""),
                                "phone":        item.get("telephone", ""),
                                "address":      addr.get("streetAddress", ""),
                                "city":         addr.get("addressLocality", ""),
                                "state":        addr.get("addressRegion", ""),
                                "zip_code":     addr.get("postalCode", ""),
                                "country":      addr.get("addressCountry", "US"),
                                "latitude":     None,
                                "longitude":    None,
                                "is_closed":    False,
                                "website":      item.get("url", ""),
                                "hours":        _json.dumps({}),
                                "image_url":    item.get("image", ""),
                                "yelp_url":     item.get("url", ""),
                                "transactions": "",
                                "created_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            })
                except Exception:
                    pass

            log.info(f"  Total so far: {len(businesses)}")
            time.sleep(random.uniform(2, 4))
    finally:
        driver.quit()

    return businesses


# ─────────────────────────────────────────────
# OPTION C: Load from JSON file
# ─────────────────────────────────────────────

def fetch_from_file(filepath: str) -> list[dict]:
    """Load pre-scraped data from yelp_businesses.json"""
    path = Path(filepath)
    if not path.exists():
        log.error(f"File not found: {filepath}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    log.info(f"Loaded {len(data)} records from {filepath}")
    return data


# ─────────────────────────────────────────────
# MySQL: Setup & Insert
# ─────────────────────────────────────────────

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def create_tables(conn):
    cursor = conn.cursor()
    sql = """
    CREATE DATABASE IF NOT EXISTS yelp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """
    cursor.execute(sql)
    cursor.execute("USE yelp_db;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS businesses (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        yelp_id         VARCHAR(255)    NOT NULL UNIQUE,
        name            VARCHAR(255)    NOT NULL,
        alias           VARCHAR(255),
        category        VARCHAR(100),
        rating          DECIMAL(2,1)    DEFAULT 0.0,
        review_count    INT             DEFAULT 0,
        price_range     VARCHAR(10),
        phone           VARCHAR(30),
        address         VARCHAR(255),
        city            VARCHAR(100),
        state           VARCHAR(50),
        zip_code        VARCHAR(20),
        country         VARCHAR(10)     DEFAULT 'US',
        latitude        DECIMAL(9,6),
        longitude       DECIMAL(9,6),
        is_closed       TINYINT(1)      DEFAULT 0,
        website         VARCHAR(500),
        hours           JSON,
        image_url       VARCHAR(500),
        yelp_url        VARCHAR(500),
        transactions    VARCHAR(255),
        created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP,
        updated_at      DATETIME        DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_city     (city),
        INDEX idx_state    (state),
        INDEX idx_category (category),
        INDEX idx_rating   (rating)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    conn.commit()
    log.info("Tables created/verified.")
    cursor.close()


INSERT_SQL = """
    INSERT INTO businesses
        (yelp_id, name, alias, category, rating, review_count,
         price_range, phone, address, city, state, zip_code, country,
         latitude, longitude, is_closed, website, hours,
         image_url, yelp_url, transactions, created_at)
    VALUES
        (%(yelp_id)s, %(name)s, %(alias)s, %(category)s, %(rating)s,
         %(review_count)s, %(price_range)s, %(phone)s, %(address)s,
         %(city)s, %(state)s, %(zip_code)s, %(country)s,
         %(latitude)s, %(longitude)s, %(is_closed)s, %(website)s,
         %(hours)s, %(image_url)s, %(yelp_url)s, %(transactions)s,
         %(created_at)s)
    ON DUPLICATE KEY UPDATE
        name         = VALUES(name),
        rating       = VALUES(rating),
        review_count = VALUES(review_count),
        updated_at   = CURRENT_TIMESTAMP;
"""


def insert_businesses(conn, businesses: list[dict]):
    cursor = conn.cursor()
    inserted = 0
    for biz in businesses:
        # Ensure hours is a JSON string
        if isinstance(biz.get("hours"), dict):
            biz["hours"] = json.dumps(biz["hours"])
        # is_closed: convert bool to int
        biz["is_closed"] = int(biz.get("is_closed", 0))
        try:
            cursor.execute(INSERT_SQL, biz)
            inserted += 1
        except mysql.connector.Error as e:
            log.warning(f"Skipping '{biz.get('name')}': {e}")
    conn.commit()
    cursor.close()
    log.info(f"Inserted/updated {inserted}/{len(businesses)} records.")
    return inserted


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    log.info("=== Yelp → MySQL Pipeline ===")

    # ── Step 1: Fetch data ───────────────────
    # Choose ONE of the options below:

    # Option A: Yelp Fusion API (recommended, requires free API key)
    if YELP_API_KEY and YELP_API_KEY != "YOUR_YELP_FUSION_API_KEY":
        log.info("Selenium scraping ...")
        # businesses = fetch_via_api(YELP_API_KEY, SEARCH_PARAMS.copy())

    # Option B: Selenium scraping (no API key needed, may get blocked)
        businesses = fetch_via_selenium("Restaurants", "New York, NY", max_pages=5)

    # Option C: Pre-scraped JSON file (guaranteed to work, use for testing)
    else:
        log.info("API key not set — loading from yelp_businesses.json ...")
        businesses = fetch_from_file(DATA_FILE)

    if not businesses:
        log.error("No data fetched. Exiting.")
        return

    log.info(f"Fetched {len(businesses)} businesses.")

    # ── Step 2: Connect to MySQL ─────────────
    try:
        conn = get_connection()
        log.info("Connected to MySQL.")
    except mysql.connector.Error as e:
        log.error(f"Cannot connect to MySQL: {e}")
        log.error("Make sure MySQL is running and DB_CONFIG is correct.")
        return

    # ── Step 3: Create tables ────────────────
    create_tables(conn)

    # ── Step 4: Insert data ──────────────────
    inserted = insert_businesses(conn, businesses)
    conn.close()

    log.info(f"Done! {inserted} records loaded into MySQL table 'businesses'.")
    log.info("Run this SQL to verify:  SELECT * FROM yelp_db.businesses LIMIT 10;")


if __name__ == "__main__":
    main()
