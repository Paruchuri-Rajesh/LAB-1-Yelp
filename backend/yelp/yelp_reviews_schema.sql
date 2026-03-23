-- ============================================================
-- Yelp Reviews Table — MySQL Schema
-- Run this AFTER yelp_schema.sql
-- ============================================================

USE yelp_db;

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


-- ============================================================
-- Sample Queries
-- ============================================================

-- All reviews for a specific business
-- SELECT r.author, r.rating, r.review_text, r.review_date
-- FROM reviews r
-- JOIN businesses b ON b.id = r.business_id
-- WHERE b.name = 'The Golden Fork'
-- ORDER BY r.review_date DESC;

-- Average rating per business with review count
-- SELECT b.name, b.city, COUNT(r.id) AS total_reviews, ROUND(AVG(r.rating), 2) AS avg_rating
-- FROM businesses b
-- JOIN reviews r ON b.id = r.business_id
-- GROUP BY b.id
-- ORDER BY avg_rating DESC, total_reviews DESC;

-- Top reviewers (most reviews written)
-- SELECT author, COUNT(*) AS total, ROUND(AVG(rating), 2) AS avg_rating
-- FROM reviews
-- GROUP BY author
-- ORDER BY total DESC
-- LIMIT 10;

-- Reviews with most useful votes
-- SELECT r.author, r.rating, r.review_text, r.useful_votes, b.name AS business
-- FROM reviews r
-- JOIN businesses b ON b.id = r.business_id
-- ORDER BY r.useful_votes DESC
-- LIMIT 10;

-- Rating distribution across all reviews
-- SELECT rating, COUNT(*) AS count,
--        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews), 1) AS pct
-- FROM reviews
-- GROUP BY rating
-- ORDER BY rating DESC;

-- Monthly review trends
-- SELECT DATE_FORMAT(review_date, '%Y-%m') AS month, COUNT(*) AS reviews
-- FROM reviews
-- GROUP BY month
-- ORDER BY month DESC;
