# Product Requirements Document (PRD)
## Yelp Prototype - Restaurant Discovery & Review Platform

---

### 1. Overview

| Field | Detail |
|-------|--------|
| **Project Name** | Yelp Prototype |
| **Tech Stack** | React (Frontend), Python FastAPI (Backend), MySQL (Database), LangChain + Tavily (AI) |
| **Due Date** | March 24, 2026, 11:59 PM |
| **Points** | 40 |

### 2. Objective

Build a full-stack Yelp-style restaurant discovery and review platform that allows users to search, review, and discover restaurants, while restaurant owners can manage listings and view analytics. The platform includes an AI-powered chatbot that delivers personalized restaurant recommendations based on user preferences and natural language queries.

### 3. User Personas

| Persona | Description |
|---------|-------------|
| **User (Reviewer)** | A consumer who searches for restaurants, writes reviews, saves favorites, and interacts with the AI assistant for personalized recommendations. |
| **Restaurant Owner** | A business owner who manages restaurant profiles, posts listings, views reviews, and monitors analytics. |

---

### 4. Functional Requirements

#### 4.1 User (Reviewer) Features

| # | Feature | Requirements | Priority |
|---|---------|-------------|----------|
| U1 | **Signup** | Name, email, password; passwords hashed with bcrypt | P0 |
| U2 | **Login/Logout** | JWT or session-based authentication | P0 |
| U3 | **Profile Page** | Display/update: name, email, phone, about me, city, country (dropdown), state (abbreviated), languages, gender; profile picture upload | P0 |
| U4 | **User Preferences** | Cuisine preferences (Italian, Chinese, Mexican, Indian, Japanese, American), price range ($-$$$$), preferred location/search radius, dietary needs (vegetarian, vegan, halal, gluten-free, kosher), ambiance (casual, fine dining, family-friendly, romantic), sort preference (rating, distance, popularity, price) | P0 |
| U5 | **Restaurant Search/Dashboard** | Search by: restaurant name, cuisine type, keywords (quiet, family-friendly, outdoor seating, wifi), location (city/zip) | P0 |
| U6 | **Restaurant Details View** | Display: name, cuisine, address, description, hours, contact info, photos, average rating, review count, list of reviews | P0 |
| U7 | **Add Restaurant Listing** | Create entry with: name, cuisine type, address/city, contact info (optional), description, hours (optional), photos (optional) | P1 |
| U8 | **Reviews** | Add/edit/delete own reviews: rating (1-5 stars), comment text, server-generated date, optional photo attachments | P0 |
| U9 | **Favorites** | Mark/unmark restaurants as favorites; display favorites tab | P1 |
| U10 | **User History** | Display history tab for previous reviews and restaurants added | P1 |
| U11 | **AI Assistant Chatbot** | Prominently accessible on home screen/dashboard (see Section 5) | P0 |

#### 4.2 Restaurant Owner Features

| # | Feature | Requirements | Priority |
|---|---------|-------------|----------|
| O1 | **Signup** | Name, email, password, restaurant location | P0 |
| O2 | **Login/Logout** | JWT or session-based authentication | P0 |
| O3 | **Profile Management** | View/update: restaurant name, cuisine type, description, location, contact info, photos, hours of operation | P0 |
| O4 | **Restaurant Posting** | Post listing with: location, description, photos, pricing tier, amenities, cuisine type, contact info, hours | P0 |
| O5 | **Claim/Manage Restaurant** | Claim existing restaurant listings and manage profiles | P1 |
| O6 | **View Reviews** | View reviews for owned restaurants (read-only, no deletion) | P1 |
| O7 | **Owner Dashboard** | Restaurant analytics, recent reviews, ratings distribution, total views, sentiment analysis | P1 |

---

### 5. AI Assistant Chatbot Requirements

#### 5.1 Core Functionality

| Requirement | Description |
|-------------|-------------|
| **Preference Loading** | Fetch user's saved preferences (cuisine, price range, dietary needs, location, ambiance) from DB on first query |
| **NLU** | Use LangChain for natural language understanding and query interpretation |
| **Information Extraction** | Extract: cuisine type, price range, dietary restrictions, occasion, ambiance from queries |
| **Database Search** | Query restaurant DB with interpreted filters |
| **Ranking** | Rank results by relevance to query + user preferences |
| **Personalization** | Provide recommendations with reasoning tied to user preferences |
| **Multi-turn Conversation** | Support follow-up questions and refinements |
| **Web Search** | Use Tavily for additional context (current hours, events, trending restaurants) |

#### 5.2 API Specification

| Field | Detail |
|-------|--------|
| **Endpoint** | `POST /ai-assistant/chat` |
| **Input** | `{ "message": "user query", "conversation_history": [...] }` |
| **Output** | Structured JSON with recommendations |

#### 5.3 Chatbot UI Requirements

- Chat window with conversation history
- Input field for user queries
- Restaurant cards with key details (name, rating, price, cuisine) — clickable to full details
- Loading/thinking indicator
- New conversation / clear chat button
- Conversational, helpful tone
- Optional: quick action buttons ("Find dinner tonight", "Best rated near me", "Vegan options")

---

### 6. Backend Requirements

#### 6.1 Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Python + FastAPI |
| Database | MySQL |
| Auth | JWT or session-based |
| Password Hashing | bcrypt |
| AI/NLU | LangChain |
| Web Search | Tavily |

#### 6.2 RESTful API Endpoints

| Category | Endpoints |
|----------|-----------|
| **Auth** | Signup, Login, Logout (User + Owner) |
| **User Profile** | Get/Update profile, Upload profile picture |
| **User Preferences** | Get/Update preferences |
| **Restaurants** | Create, Read, Update, Search, Filter |
| **Reviews** | Create (linked to restaurant + user), List (by restaurant), Update (own only), Delete (own only) |
| **Favorites** | Add/Remove favorite, List favorites |
| **Owner Dashboard** | Analytics, recent reviews |
| **AI Assistant** | `POST /ai-assistant/chat` |

#### 6.3 Security & Error Handling

- Secure API endpoints with validation
- Proper exception handling with meaningful error responses
- Input sanitization

---

### 7. Frontend Requirements

#### 7.1 Pages

**Public Pages:**

| Page | Description |
|------|-------------|
| Explore/Search Page | Landing page with search, filters, restaurant cards |
| Restaurant Details Page | Full restaurant view with reviews, ratings, photos |

**User Pages (Authenticated):**

| Page | Description |
|------|-------------|
| Signup/Login | Auth forms with validation and error handling |
| Profile + Preferences Editor | Profile management + AI preference configuration |
| Add Restaurant Form | Create new restaurant listing with photo upload |
| Write Review Form | Review submission with star rating and comments |
| AI Assistant Interface | Chat interface on home screen / explore page |

**Owner Pages (Authenticated):**

| Page | Description |
|------|-------------|
| Signup/Login | Owner auth with validation |
| Restaurant Profile Management | View/update restaurant details |
| Add/Edit Restaurant Form | Post or edit listings with photos, pricing, amenities |
| Claim Restaurant | Claim existing listings |
| Reviews Dashboard | Read-only review viewer with filtering/sorting |
| Owner Analytics Dashboard | Performance metrics, ratings distribution, sentiment |

#### 7.2 Frontend Standards

| Standard | Requirements |
|----------|-------------|
| **Responsive Design** | Mobile, tablet, desktop; use Bootstrap or TailwindCSS |
| **API Integration** | Axios or Fetch API; error handling; loading states |
| **Architecture** | Separation of concerns (components/pages/services); reusable components; organized folder structure |
| **Accessibility** | Semantic HTML, alt text, keyboard navigation |

---

### 8. Non-Functional Requirements

| Requirement | Description |
|-------------|-------------|
| **Responsiveness** | Works on mobile, tablet, and desktop |
| **Accessibility** | Semantic HTML, alt text, keyboard navigation |
| **Scalability** | Optimized queries, efficient API response times, no unnecessary data loading |
| **API Documentation** | Swagger UI (testable) OR exported Postman collection with descriptions, params, headers, sample responses |

---

### 9. Deliverables

| Deliverable | Details |
|-------------|---------|
| **Source Code** | Private GitHub repo; invite `Devdatta1999` and `Saurabh2504` |
| **Commit History** | Detailed commit messages describing changes |
| **README.md** | Instructions to run the application |
| **requirements.txt** | Python dependencies (no venv or __pycache__) |
| **API Docs** | Swagger UI or Postman collection |
| **Project Report** | `YourName_Lab1_Report.doc` uploaded to Canvas |

#### 9.1 Report Contents

- **Introduction:** Purpose and goals
- **System Design:** Architecture overview (FastAPI, MySQL, React, AI Service)
- **AI Implementation:** How chatbot interprets queries and uses preferences
- **Results:** Screenshots of key screens + API test results

---

### 10. Data Models (High-Level)

#### Users
| Field | Type | Notes |
|-------|------|-------|
| id | INT | Primary key, auto-increment |
| name | VARCHAR | Required |
| email | VARCHAR | Unique, required |
| password_hash | VARCHAR | bcrypt hashed |
| role | ENUM | 'user' / 'owner' |
| phone | VARCHAR | Optional |
| about_me | TEXT | Optional |
| city | VARCHAR | Optional |
| state | VARCHAR | Abbreviated |
| country | VARCHAR | Dropdown |
| languages | VARCHAR | Optional |
| gender | VARCHAR | Optional |
| profile_picture | VARCHAR | File path/URL |

#### User Preferences
| Field | Type | Notes |
|-------|------|-------|
| id | INT | Primary key |
| user_id | INT | FK to Users |
| cuisine_preferences | JSON | Array of cuisines |
| price_range | VARCHAR | $, $$, $$$, $$$$ |
| preferred_locations | JSON | Locations / search radius |
| dietary_needs | JSON | Array of restrictions |
| ambiance_preferences | JSON | Array of ambiance types |
| sort_preference | VARCHAR | rating/distance/popularity/price |

#### Restaurants
| Field | Type | Notes |
|-------|------|-------|
| id | INT | Primary key |
| owner_id | INT | FK to Users (nullable) |
| name | VARCHAR | Required |
| cuisine_type | VARCHAR | Required |
| description | TEXT | Optional |
| address | VARCHAR | Required |
| city | VARCHAR | Required |
| zip_code | VARCHAR | Optional |
| contact_info | VARCHAR | Optional |
| hours | JSON | Optional |
| pricing_tier | VARCHAR | $-$$$$ |
| amenities | JSON | Optional |
| photos | JSON | Array of URLs |

#### Reviews
| Field | Type | Notes |
|-------|------|-------|
| id | INT | Primary key |
| user_id | INT | FK to Users |
| restaurant_id | INT | FK to Restaurants |
| rating | INT | 1-5 |
| comment | TEXT | Required |
| date | DATETIME | Server-generated |
| photos | JSON | Optional |

#### Favorites
| Field | Type | Notes |
|-------|------|-------|
| id | INT | Primary key |
| user_id | INT | FK to Users |
| restaurant_id | INT | FK to Restaurants |

---

### 11. Reference

- Yelp website for UI/UX inspiration: https://www.yelp.com/
- Tavily for web search integration: https://www.tavily.com/#features
