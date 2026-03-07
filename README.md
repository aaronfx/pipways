# Pipways Trading Education Platform

Complete single-file FastAPI application with AI-powered trading analysis and education features.

## Features

### 1. AI Chart Analysis
- Upload trading chart screenshots
- AI grades your setup (A/B/C)
- Identifies entry/exit points
- Risk/reward analysis
- Improvement suggestions

### 2. AI Performance Analysis
- Upload trading statements (PDF/CSV)
- AI identifies trader type (Scalper, Day Trader, FOMO Trader, etc.)
- Strengths and weaknesses analysis
- Psychology profile
- Personalized recommendations

### 3. AI Mentor (NEW)
- Personalized trading coach
- Remembers your performance history
- References your specific mistakes
- Suggests relevant courses
- Accountability partner

### 4. Webinars (Zoom Integration)
- Schedule live trading sessions
- Auto-generate Zoom meetings
- User registration system
- Email reminders (future feature)

### 5. LMS (Learning Management System)
- Structured trading courses
- Video and text content
- Progress tracking
- AI-recommended learning paths

### 6. Blog (WordPress-Style)
- Visual editor with blocks
- SEO optimization (meta tags, scoring)
- Categories and tags
- XML sitemap generation
- Featured images
- Draft/publish workflow

### 7. Admin Dashboard
- Manage all content
- View user statistics
- Create/edit courses
- Schedule webinars
- Write blog posts

## File Structure

```
pipways/
├── main.py              # Complete application (~1000 lines)
├── requirements.txt     # Dependencies
├── render.yaml          # Render deployment config
├── 
│   └── index.html       # Your frontend (upload separately)
└── README.md           # This file
```

## Deployment

### 1. Environment Variables

Set these in Render dashboard:

```
DATABASE_URL=postgresql://... (auto-set by Render)
SECRET_KEY=your-random-secret-key
OPENROUTER_API_KEY=sk-or-v1-... (from openrouter.ai)
ZOOM_API_KEY=... (optional, for auto-meeting creation)
ZOOM_API_SECRET=... (optional)
```

### 2. Deploy to Render

1. Push all files to GitHub
2. Connect repo to Render
3. Render will use `render.yaml` for auto-configuration
4. Database tables auto-created on first run

### 3. Default Admin

Auto-created on first startup:
- Email: `admin@pipways.com`
- Password: `admin123`

**Change this immediately after first login!**

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login

### AI Analysis
- `POST /analyze/chart` - Analyze chart image
- `GET /analyze/chart/history` - Get history
- `POST /analyze/performance` - Analyze statement
- `GET /analyze/performance/history` - Get history

### AI Mentor
- `POST /mentor/chat` - Chat with AI mentor
- `GET /mentor/history` - Chat history
- `GET /mentor/insights` - Trader profile

### Webinars
- `GET /webinars` - List upcoming
- `POST /webinars/{id}/register` - Register
- `GET /webinars/my` - My registrations
- `POST /admin/webinars` - Create (admin)

### LMS
- `GET /courses` - List courses
- `GET /courses/{id}` - Course details
- `POST /courses/{id}/modules/{id}/complete` - Complete module
- `GET /courses/recommended` - AI recommendations
- `POST /admin/courses` - Create course (admin)
- `POST /admin/courses/{id}/modules` - Add module (admin)

### Blog
- `GET /blog/posts` - List posts
- `GET /blog/posts/{slug}` - Single post
- `GET /blog/categories` - List categories
- `GET /blog/tags` - List tags
- `GET /blog/sitemap.xml` - SEO sitemap
- `POST /admin/blog/posts` - Create post (admin)
- `PUT /admin/blog/posts/{id}` - Update post (admin)

### Admin
- `GET /admin/stats` - Dashboard stats
- `GET /admin/users` - List users

## Database Schema

### Core Tables
- `users` - Authentication
- `chart_analyses` - Chart uploads
- `performance_analyses` - Statement analyses
- `mentorship_sessions` - AI chat history
- `user_insights` - AI-generated profiles

### Education Tables
- `courses` - Course metadata
- `course_modules` - Lessons
- `user_progress` - Completion tracking

### Event Tables
- `webinars` - Session info
- `webinar_registrations` - Signups

### Content Tables
- `blog_posts` - Articles with SEO
- `blog_categories` - Categories
- `blog_tags` - Tags
- `post_categories` - Relationships
- `post_tags` - Relationships

## Frontend Integration

Your frontend should:

1. **Store auth token** after login
2. **Include token** in all requests:
   ```javascript
   headers: {
     'Authorization': 'Bearer ' + token,
     'Content-Type': 'application/json'
   }
   ```
3. **Handle 401 errors** by redirecting to login
4. **Use FormData** for file uploads

## Security Notes

- All passwords hashed with bcrypt
- JWT tokens expire in 30 days
- Admin routes protected
- SQL injection prevented (parameterized queries)
- CORS enabled for all origins (restrict in production)

## Support

For issues:
1. Check `/health` endpoint
2. Check Render logs
3. Verify environment variables
4. Ensure database is connected

## License

Private - For Pipways use only
