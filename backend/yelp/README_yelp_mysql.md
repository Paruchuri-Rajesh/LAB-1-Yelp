# Yelp → MySQL Data Pipeline

## Files Included

| File | Description |
|------|-------------|
| `yelp_scraper.py` | Main Python scraper + MySQL loader |
| `yelp_schema.sql` | MySQL schema (CREATE TABLE statements) |
| `yelp_businesses.json` | Pre-scraped sample data (50 businesses) |
| `yelp_businesses.csv` | Same data in CSV format |

---

## Quick Start

### 1. Install Dependencies

```bash
pip install requests beautifulsoup4 mysql-connector-python
# For Selenium option:
pip install selenium webdriver-manager
```

### 2. Create MySQL Database & Tables

```bash
mysql -u root -p < yelp_schema.sql
```

Or paste the contents of `yelp_schema.sql` into MySQL Workbench / phpMyAdmin.

### 3. Configure the Script

Edit `yelp_scraper.py` and update `DB_CONFIG`:

```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",          # Your MySQL username
    "password": "your_password", # Your MySQL password
    "database": "yelp_db",
}
```

### 4. Run the Script

```bash
python yelp_scraper.py
```

By default (no API key), it loads the 50 pre-scraped businesses from `yelp_businesses.json` into MySQL.

---

## Data Source Options

### Option A — Yelp Fusion API *(Recommended)*

1. Register for a free API key at https://www.yelp.com/developers/v3/manage_app
2. Set `YELP_API_KEY = "your_actual_key"` in the script
3. Free tier: **500 API calls/day**, 50 results per call → up to **25,000 records/day**

### Option B — Selenium Scraping

Uncomment the Selenium section in `main()`. Note:
- Yelp uses **DataDome** anti-bot protection
- Use a residential proxy for better success rate
- Add random delays between requests

```python
businesses = fetch_via_selenium("Restaurants", "New York, NY", max_pages=10)
```

### Option C — Pre-Scraped File *(Default)*

Works out of the box. Uses `yelp_businesses.json` included with this package.

---

## MySQL Schema

```sql
TABLE businesses (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    yelp_id       VARCHAR(255) UNIQUE,
    name          VARCHAR(255),
    alias         VARCHAR(255),
    category      VARCHAR(100),
    rating        DECIMAL(2,1),
    review_count  INT,
    price_range   VARCHAR(10),
    phone         VARCHAR(30),
    address       VARCHAR(255),
    city          VARCHAR(100),
    state         VARCHAR(50),
    zip_code      VARCHAR(20),
    country       VARCHAR(10),
    latitude      DECIMAL(9,6),
    longitude     DECIMAL(9,6),
    is_closed     TINYINT(1),
    website       VARCHAR(500),
    hours         JSON,
    image_url     VARCHAR(500),
    yelp_url      VARCHAR(500),
    transactions  VARCHAR(255),
    created_at    DATETIME,
    updated_at    DATETIME
)
```

---

## Useful SQL Queries

```sql
-- Top 10 rated restaurants
SELECT name, city, state, rating, review_count, category
FROM businesses
WHERE is_closed = 0
ORDER BY rating DESC, review_count DESC
LIMIT 10;

-- Count by category
SELECT category, COUNT(*) as total, ROUND(AVG(rating), 2) as avg_rating
FROM businesses
GROUP BY category
ORDER BY total DESC;

-- Filter by city and price
SELECT name, rating, price_range, phone
FROM businesses
WHERE city = 'New York' AND price_range IN ('$', '$$')
ORDER BY rating DESC;

-- Businesses by state
SELECT state, COUNT(*) as total
FROM businesses
GROUP BY state
ORDER BY total DESC;
```

---

## Load CSV Directly into MySQL

If you prefer to skip Python entirely, import the CSV directly:

```sql
LOAD DATA INFILE '/path/to/yelp_businesses.csv'
INTO TABLE yelp_db.businesses
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

> **Note:** Make sure `secure_file_priv` is configured in MySQL for `LOAD DATA INFILE`.
