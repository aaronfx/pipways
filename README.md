# Pipways - Modular Structure

Organized, maintainable version of your working trading platform.

## Structure

```
pipways/
├── main.py              # Entry point (100 lines)
├── config.py            # Settings & constants
├── database.py          # DB connection & migrations
├── auth.py              # Authentication (200 lines)
├── routers/             # Feature modules
│   ├── trades.py        # Trading journal
│   ├── analysis.py      # AI chart & file analysis
│   ├── mentorship.py    # AI mentor
│   ├── blog.py          # Blog system
│   └── admin.py         # Admin dashboard
├── services/            # Business logic
│   ├── openrouter.py    # AI API calls
│   ├── file_processor.py # PDF/CSV parsing
│   └── analyzer.py      # Trade analysis logic
├── static/
│   └── index.html       # Your working frontend
├── requirements.txt
└── render.yaml
```

## Deployment

1. **Upload to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial modular structure"
   git push origin main
   ```

2. **Deploy to Render:**
   - Connect GitHub repo
   - Render will use `render.yaml` auto-configuration
   - Database auto-provisioned

3. **Environment Variables:**
   - `SECRET_KEY`: Auto-generated
   - `DATABASE_URL`: Auto-configured
   - `OPENROUTER_API_KEY`: Add manually for AI features

## Adding New Features

Example: Add "notifications"

1. **Create `routers/notifications.py`:**
   ```python
   from fastapi import APIRouter
   router = APIRouter()

   @router.get("/")
   async def get_notifications():
       return {"notifications": []}
   ```

2. **Add to `main.py`:**
   ```python
   from routers import notifications
   app.include_router(notifications.router, prefix="/notifications")
   ```

3. **Add table in `database.py`:**
   ```python
   await conn.execute("""
       CREATE TABLE IF NOT EXISTS notifications (
           id SERIAL PRIMARY KEY,
           user_id INTEGER REFERENCES users(id),
           message TEXT
       )
   """)
   ```

Done! No need to touch other files.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /auth/login` | Login |
| `POST /auth/register` | Register |
| `GET /trades/` | Get trades |
| `POST /trades/` | Create trade |
| `POST /analyze/chart` | Analyze chart image |
| `POST /analyze/trade-file` | Analyze statement |
| `POST /mentorship/personalized` | AI mentor |
| `GET /blog/posts` | List posts |
| `GET /admin/dashboard` | Admin stats |

## Default Login
- Email: `admin@pipways.com`
- Password: `admin123`
