# Yelp Prototype - Updated Build

This version includes:
- a Yelp-like search/results UI in React
- Yelp Fusion API import support for restaurants, place/location metadata, hours, photos, and review snippets
- owner signup + restaurant claim flow
- owner dashboards with views, review counts, ratings, and recent reviews
- MySQL setup without Docker

## Important Yelp API note
Yelp Fusion is great for seeding and refreshing restaurant data, but the public API only exposes a **small set of review snippets per business** rather than a restaurant's full review history. This project imports those snippets into MySQL and keeps normal in-app user reviews in the same database as separate `local` reviews.

## Backend setup (no Docker)

### 1. Install MySQL locally
Install MySQL Community Server and MySQL Shell / MySQL Workbench from MySQL's official downloads.

### 2. Create the database
Open a terminal and run:

```bash
mysql -u root -p < backend/mysql/create_database.sql
```

### 3. Create and activate a Python virtual environment
From `backend/`:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 4. Install Python packages

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables
Copy `.env.example` to `.env` and update it. Example:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/yelp_db?charset=utf8mb4
SECRET_KEY=replace_me
ALLOWED_ORIGINS=["http://localhost:5173"]
YELP_API_KEY=your_yelp_fusion_api_key
```

### 6. Create tables
From `backend/`:

```bash
python -m app.create_tables
```

### 7. Import Yelp data into MySQL
Example:

```bash
python -m seeds.seed_yelp --location "Union City, CA" --term "restaurants" --limit 25
```

Or use the API endpoint:

```http
POST /api/v1/restaurants/import/yelp
```

Body:

```json
{
  "location": "Union City, CA",
  "term": "restaurants",
  "limit": 25
}
```

### 8. Start FastAPI

```bash
uvicorn app.main:app --reload
```

Swagger will be available at:
- `http://127.0.0.1:8000/docs`

## Frontend setup
From `frontend/`:

```bash
npm install
npm run dev
```

## New owner flow
1. Sign up with `Owner` account type.
2. Import Yelp restaurants or use existing restaurant rows.
3. Claim a restaurant from the owner dashboard.
4. Open the owner dashboard to view analytics and recent reviews.

## Key API endpoints
- `GET /api/v1/restaurants`
- `GET /api/v1/restaurants/places`
- `GET /api/v1/restaurants/{id}`
- `POST /api/v1/restaurants/import/yelp`
- `POST /api/v1/restaurants/{id}/reviews`
- `GET /api/v1/owner/dashboard`
- `POST /api/v1/owner/restaurants/{id}/claim`
- `GET /api/v1/owner/restaurants/{id}/dashboard`
- `PUT /api/v1/owner/restaurants/{id}`

## Notes
- Restaurant detail page views are tracked in `restaurant_views`.
- Imported Yelp review snippets are stored with `source = "yelp"`.
- In-app reviews are stored with `source = "local"` and linked to authenticated users.
