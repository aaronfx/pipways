# Pipways Complete - Quick Start Guide

## 🚀 What You Got

A **single-file FastAPI application** (main.py, ~1250 lines) containing:

### AI Features
1. **Chart Analysis** - Upload trading charts, get AI grades (A/B/C)
2. **Performance Analysis** - Upload statements, get trader profile
3. **AI Mentor** - Chatbot that remembers your weaknesses & recommends courses

### Education Features
4. **Webinars** - Schedule Zoom meetings, user registration
5. **LMS** - Create courses, track progress, AI-recommended learning paths
6. **Blog** - WordPress-style editor with SEO scoring (0-100)

### Admin Features
7. **Dashboard** - View stats, manage all content
8. **User Management** - List all users

## 📦 Files

```
pipways_complete/
├── main.py          ← Everything is here (46KB)
├── requirements.txt ← Dependencies
├── render.yaml      ← Auto-deployment config
├── 
│   └── index.html   ← Replace with your frontend
└── README.md        ← Full documentation
```

## ⚡ Deployment (3 Steps)

### Step 1: Upload to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

### Step 2: Connect to Render
1. Go to [render.com](https://render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repo
4. Render auto-detects `render.yaml`

### Step 3: Set Environment Variables
In Render dashboard, add:
```
OPENROUTER_API_KEY=sk-or-v1-... (from openrouter.ai)
ZOOM_API_KEY=... (optional)
ZOOM_API_SECRET=... (optional)
```

**Done!** Database and admin user auto-created on first run.

## 🔑 Default Login
- **Email:** `admin@pipways.com`
- **Password:** `admin123`

**Change this immediately!**

## 🔌 API Base URL
```javascript
const API_URL = window.location.origin;  // Auto-detects
```

## 📊 Database Tables (16 total)

**Core:**
- users, chart_analyses, performance_analyses

**AI Mentor:**
- mentorship_sessions, user_insights

**Webinars:**
- webinars, webinar_registrations

**LMS:**
- courses, course_modules, user_progress

**Blog:**
- blog_posts, blog_categories, blog_tags
- post_categories, post_tags, media_files

## 🎯 Key API Endpoints

### Auth
```
POST /auth/login
POST /auth/register
```

### AI Analysis
```
POST /analyze/chart (multipart: file, pair, timeframe)
POST /analyze/performance (multipart: file)
```

### AI Mentor
```
POST /mentor/chat (form: message)
GET /mentor/insights
```

### Webinars
```
GET /webinars
POST /webinars/{id}/register
POST /admin/webinars (admin only)
```

### LMS
```
GET /courses
GET /courses/{id}
POST /courses/{id}/modules/{id}/complete
GET /courses/recommended
```

### Blog
```
GET /blog/posts
GET /blog/posts/{slug}
GET /blog/sitemap.xml
POST /admin/blog/posts (admin only)
```

## 🛠️ Customization

### Add Your Frontend
Replace `index.html` with your actual frontend.

### Modify AI Behavior
Edit the prompts in:
- `analyze_chart()` (line ~300)
- `analyze_performance()` (line ~350)
- `mentor_chat()` (line ~420)

### Add New Features
Just add new routes to `main.py`:
```python
@app.post("/new-feature")
async def new_feature():
    return {"message": "Hello"}
```

## 🔒 Security

- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens (30-day expiry)
- ✅ Admin route protection
- ✅ SQL injection prevention
- ✅ CORS enabled

## 🐛 Troubleshooting

**Issue:** "ModuleNotFoundError"
**Fix:** Check `requirements.txt` is uploaded

**Issue:** Database connection fails
**Fix:** Check `DATABASE_URL` in Render dashboard

**Issue:** AI analysis fails
**Fix:** Check `OPENROUTER_API_KEY` is set

**Issue:** "Invalid email or password"
**Fix:** Database was reset, admin will be recreated automatically

## 📈 Next Steps

1. ✅ Deploy backend
2. ⬜ Upload your frontend
3. ⬜ Customize AI prompts
4. ⬜ Add content (courses, blog posts)
5. ⬜ Configure Zoom (optional)
6. ⬜ Go live!

## 💡 Pro Tips

- **AI Mentor** works best after user completes performance analysis
- **Blog SEO** score appears when creating posts (aim for 80+)
- **Course recommendations** auto-generated from performance analysis
- **Zoom meetings** auto-created if API keys provided

## 📞 Support

Check `/health` endpoint for status.

Full docs in `README.md`
