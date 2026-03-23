-- ============================================================
-- Yelp Business Data - MySQL Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS yelp_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE yelp_db;

-- ============================================================
-- Table: businesses
-- ============================================================
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

    INDEX idx_city      (city),
    INDEX idx_state     (state),
    INDEX idx_category  (category),
    INDEX idx_rating    (rating),
    INDEX idx_is_closed (is_closed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- Table: reviews  (optional - for review-level data)
-- ============================================================
CREATE TABLE IF NOT EXISTS reviews (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    business_id     INT             NOT NULL,
    review_text     TEXT,
    rating          DECIMAL(2,1),
    author          VARCHAR(255),
    review_date     DATE,
    created_at      DATETIME        DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    INDEX idx_business_id (business_id),
    INDEX idx_review_date (review_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- Useful Queries
-- ============================================================

-- Top rated restaurants
-- SELECT name, city, state, rating, review_count, category
-- FROM businesses
-- WHERE is_closed = 0
-- ORDER BY rating DESC, review_count DESC
-- LIMIT 10;

-- Businesses by city
-- SELECT city, COUNT(*) AS total, AVG(rating) AS avg_rating
-- FROM businesses
-- GROUP BY city
-- ORDER BY total DESC;

-- Filter by category and price
-- SELECT * FROM businesses
-- WHERE category = 'Italian' AND price_range IN ('$', '$$')
-- ORDER BY rating DESC;
