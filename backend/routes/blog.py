"""
Blog Routes - SEO Optimized CMS with Yoast-style scoring
Includes: Rich content, SEO analysis, media management, slugs
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import json
import math

from . import database
from .security import get_current_user, get_current_user_optional, get_admin_user
from .schemas import (
    BlogPostCreate, BlogPostUpdate, BlogPostResponse, BlogPostMinimal,
    BlogListResponse, BlogSEOBase, BlogMediaBase
)

router = APIRouter()

def generate_slug(title: str) -> str:
    """Generate URL-friendly slug"""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:255]

def extract_images_from_content(content: str) -> List[str]:
    """Extract image URLs from markdown/html content"""
    pattern = r'!\[.*?\]\((.*?)\)'
    return re.findall(pattern, content)

def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())

def calculate_seo_score(content: str, title: str, meta_desc: str, focus_keyword: str) -> Dict[str, Any]:
    """
    Calculate SEO score (0-100) similar to Yoast SEO
    Returns score and recommendations
    """
    if not focus_keyword:
        return {"score": 0, "recommendations": ["Add a focus keyword"], "keyword_density": 0}
    
    score = 0
    recommendations = []
    content_lower = content.lower()
    title_lower = title.lower()
    meta_lower = (meta_desc or "").lower()
    keyword_lower = focus_keyword.lower()
    word_count = count_words(content)
    
    # 1. Keyword in title (15 points)
    if keyword_lower in title_lower:
        score += 15
        # Bonus for keyword at beginning
        if title_lower.startswith(keyword_lower):
            score += 5
    else:
        recommendations.append(f"Add focus keyword '{focus_keyword}' to the SEO title")
    
    # 2. Keyword in meta description (10 points)
    if meta_desc and keyword_lower in meta_lower:
        score += 10
    else:
        recommendations.append("Add focus keyword to meta description")
    
    # 3. Keyword density (15 points) - optimal 0.5% to 2.5%
    keyword_count = content_lower.count(keyword_lower)
    density = (keyword_count / word_count * 100) if word_count > 0 else 0
    
    if 0.5 <= density <= 2.5:
        score += 15
    elif density > 2.5:
        score += 5
        recommendations.append(f"Keyword density ({density:.1f}%) is too high. Reduce to avoid stuffing")
    else:
        score += 5
        recommendations.append(f"Keyword density ({density:.1f}%) is low. Add keyword more naturally")
    
    # 4. Content length (15 points) - optimal 300+ words
    if word_count >= 1000:
        score += 15
    elif word_count >= 600:
        score += 10
    elif word_count >= 300:
        score += 5
    else:
        recommendations.append(f"Content is too short ({word_count} words). Aim for at least 300 words")
    
    # 5. Headings structure (10 points)
    h2_count = len(re.findall(r'<h2', content_lower))
    h3_count = len(re.findall(r'<h3', content_lower))
    
    if h2_count > 0:
        score += 5
    else:
        recommendations.append("Add H2 headings to structure content")
    
    if h3_count > 0:
        score += 5
    
    # 6. Internal links (10 points)
    internal_links = len(re.findall(r'href=["\']/', content))
    if internal_links >= 2:
        score += 10
    elif internal_links == 1:
        score += 5
        recommendations.append("Add more internal links (at least 2 recommended)")
    else:
        recommendations.append("Add internal links to other posts")
    
    # 7. Images with alt text (10 points)
    images = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
    images_with_alt = len(re.findall(r'<img[^>]*alt=["\'][^"\']+["\'][^>]*>', content, re.IGNORECASE))
    
    if images:
        if images_with_alt == len(images):
            score += 10
        else:
            score += 5
            recommendations.append("Add alt text to all images")
    else:
        recommendations.append("Add images to improve engagement")
    
    # 8. Meta description length (5 points) - optimal 120-160 chars
    meta_len = len(meta_desc) if meta_desc else 0
    if 120 <= meta_len <= 160:
        score += 5
    elif meta_len > 160:
        recommendations.append("Meta description is too long (keep under 160 characters)")
    else:
        recommendations.append("Meta description is too short (aim for 120-160 characters)")
    
    # 9. URL/Slug optimization (5 points)
    # Handled separately in slug generation
    
    # 10. Readability indicators (10 points)
    paragraphs = content.split('</p>')
    avg_paragraph_length = sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
    
    if avg_paragraph_length < 300:  # Short paragraphs are better
        score += 5
    else:
        recommendations.append("Break long paragraphs into shorter ones for readability")
    
    # Check for transition words (simplified)
    transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently', 'first', 'second', 'finally']
    has_transitions = any(word in content_lower for word in transition_words)
    if has_transitions:
        score += 5
    
    # Ensure score is 0-100
    score = max(0, min(100, score))
    
    # Determine indicator
    if score >= 80:
        indicator = "green"
    elif score >= 50:
        indicator = "orange"
    else:
        indicator = "red"
    
    return {
        "score": score,
        "indicator": indicator,
        "keyword_density": round(density, 2),
        "word_count": word_count,
        "recommendations": recommendations if recommendations else ["Great job! Your SEO looks good."]
    }

@router.get("", response_model=BlogListResponse)
async def get_posts(
    status: Optional[str] = "published",
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get blog posts with filtering"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        query = """
            SELECT b.*, u.full_name as author_name, bd.slug, bd.seo_score 
            FROM blog_posts b 
            LEFT JOIN users u ON b.author_id = u.id 
            LEFT JOIN blog_seo_data bd ON b.id = bd.post_id
            WHERE 1=1
        """
        params = []
        param_idx = 1
        
        # Status filtering
        if current_user and current_user.get('role') in ['admin', 'moderator']:
            if status:
                query += f" AND b.status = ${param_idx}"
                params.append(status)
                param_idx += 1
        else:
            query += f" AND b.status = 'published'"
            # Premium content check
            if not current_user or current_user.get('subscription_tier') != 'vip':
                query += f" AND b.is_premium = FALSE"
            param_idx += 2
        
        if category:
            query += f" AND b.category = ${param_idx}"
            params.append(category)
            param_idx += 1
        
        if tag:
            query += f" AND $${param_idx} = ANY(b.tags)"
            params.append(tag)
            param_idx += 1
        
        if search:
            query += f" AND (b.title ILIKE ${param_idx} OR b.content ILIKE ${param_idx} OR b.excerpt ILIKE ${param_idx})"
            params.append(f"%{search}%")
            param_idx += 1
        
        # Get total count
        count_query = query.replace("b.*, u.full_name as author_name, bd.slug, bd.seo_score", "COUNT(*)")
        total = await conn.fetchval(count_query, *params)
        
        # Add pagination
        query += f" ORDER BY b.created_at DESC OFFSET ${param_idx} LIMIT ${param_idx + 1}"
        params.append((page - 1) * limit)
        params.append(limit)
        
        posts = await conn.fetch(query, *params)
        
        result = []
        for post in posts:
            post_dict = {
                "id": post['id'],
                "title": post['title'],
                "excerpt": post['excerpt'],
                "category": post['category'],
                "featured_image": post['featured_image'],
                "views": post['views'],
                "likes": post['likes'],
                "created_at": post['created_at'],
                "author_name": post['author_name'],
                "slug": post['slug']
            }
            result.append(post_dict)
        
        return {
            "posts": result,
            "total": total,
            "page": page,
            "pages": (total + limit - 1) // limit
        }

@router.get("/categories")
async def get_categories(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get all blog categories with post counts"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        categories = await conn.fetch("""
            SELECT category, COUNT(*) as count 
            FROM blog_posts 
            WHERE status = 'published'
            GROUP BY category 
            ORDER BY count DESC
        """)
        return [dict(c) for c in categories]

@router.get("/tags")
async def get_tags(current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Get all popular tags"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        # Unnest tags and count
        tags = await conn.fetch("""
            SELECT tag, COUNT(*) as count FROM (
                SELECT unnest(tags) as tag FROM blog_posts WHERE status = 'published'
            ) t
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 50
        """)
        return [dict(t) for t in tags]

@router.get("/{post_id}", response_model=BlogPostResponse)
async def get_post(
    post_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get single post with related posts"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        post = await conn.fetchrow("""
            SELECT b.*, u.full_name as author_name, u.id as author_id
            FROM blog_posts b 
            LEFT JOIN users u ON b.author_id = u.id 
            WHERE b.id = $1
        """, post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check access
        if post['status'] != 'published':
            if not current_user or current_user.get('role') not in ['admin', 'moderator']:
                raise HTTPException(status_code=404, detail="Post not found")
        
        if post['is_premium']:
            if not current_user or (current_user.get('role') not in ['admin', 'moderator'] and 
                                   current_user.get('subscription_tier') != 'vip'):
                raise HTTPException(status_code=403, detail="VIP access required")
        
        post_dict = dict(post)
        post_dict['author'] = post['author_name']
        
        # Increment views
        await conn.execute("UPDATE blog_posts SET views = views + 1 WHERE id = $1", post_id)
        post_dict['views'] += 1
        
        # Get media
        media = await conn.fetch("""
            SELECT * FROM blog_media WHERE post_id = $1 ORDER BY sort_order
        """, post_id)
        post_dict['media'] = [dict(m) for m in media]
        
        # Get SEO data
        seo = await conn.fetchrow("""
            SELECT * FROM blog_seo_data WHERE post_id = $1
        """, post_id)
        if seo:
            post_dict['seo'] = dict(seo)
        
        # Get related posts (same category, exclude current)
        related = await conn.fetch("""
            SELECT id, title, featured_image, created_at, bd.slug 
            FROM blog_posts b
            LEFT JOIN blog_seo_data bd ON b.id = bd.post_id
            WHERE category = $1 AND id != $2 AND status = 'published'
            ORDER BY created_at DESC LIMIT 3
        """, post['category'], post_id)
        post_dict['related_posts'] = [dict(r) for r in related]
        
        return post_dict

@router.get("/by-slug/{slug}")
async def get_post_by_slug(
    slug: str,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Get post by SEO slug"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        seo_data = await conn.fetchrow("""
            SELECT post_id FROM blog_seo_data WHERE slug = $1
        """, slug)
        
        if not seo_data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return await get_post(seo_data['post_id'], current_user)

@router.post("", response_model=BlogPostResponse)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    excerpt: Optional[str] = Form(None),
    category: str = Form("General"),
    status: str = Form("draft"),
    is_premium: bool = Form(False),
    featured_image: Optional[str] = Form(None),
    seo_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    focus_keyword: Optional[str] = Form(None),
    secondary_keywords: Optional[str] = Form(None),  # comma separated
    canonical_url: Optional[str] = Form(None),
    schema_markup: Optional[str] = Form(None),
    current_user: dict = Depends(get_admin_user)
):
    """Create blog post with SEO analysis"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Generate excerpt if not provided
    if not excerpt:
        excerpt = content[:200] + "..." if len(content) > 200 else content
    
    # Calculate reading time (average 200 words per minute)
    word_count = len(content.split())
    reading_time = math.ceil(word_count / 200)
    
    # Calculate SEO score
    seo_analysis = calculate_seo_score(content, seo_title or title, meta_description, focus_keyword or "")
    
    async with database.db_pool.acquire() as conn:
        async with conn.transaction():
            # Create post
            post_id = await conn.fetchval("""
                INSERT INTO blog_posts (
                    title, content, excerpt, category, author_id, status, is_premium, 
                    featured_image, reading_time_minutes, meta_keywords, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_TIMESTAMP)
                RETURNING id
            """, title, content, excerpt, category, current_user['id'], status, 
                is_premium, featured_image, reading_time, 
                secondary_keywords.split(',') if secondary_keywords else [])
            
            # Generate slug
            base_slug = generate_slug(title)
            slug = base_slug
            
            # Check uniqueness and append number if needed
            existing = await conn.fetchval("""
                SELECT 1 FROM blog_seo_data WHERE slug = $1
            """, slug)
            
            if existing:
                slug = f"{base_slug}-{post_id}"
            
            # Parse schema markup if provided
            schema_json = None
            if schema_markup:
                try:
                    schema_json = json.loads(schema_markup)
                except:
                    pass
            
            # Create SEO entry
            await conn.execute("""
                INSERT INTO blog_seo_data (
                    post_id, seo_title, meta_description, focus_keyword, secondary_keywords,
                    slug, canonical_url, schema_markup, seo_score, keyword_density, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, CURRENT_TIMESTAMP)
            """, post_id, seo_title or title, meta_description, focus_keyword,
                secondary_keywords.split(',') if secondary_keywords else [],
                slug, canonical_url, json.dumps(schema_json) if schema_json else None,
                seo_analysis['score'], seo_analysis['keyword_density'])
            
            # Auto-extract and save images from content
            images = extract_images_from_content(content)
            for idx, img_url in enumerate(images):
                await conn.execute("""
                    INSERT INTO blog_media (post_id, url, filename, alt_text, sort_order)
                    VALUES ($1, $2, $3, $4, $5)
                """, post_id, img_url, img_url.split('/')[-1], title, idx)
        
        # Return created post
        return await get_post(post_id, current_user)

@router.put("/{post_id}")
async def update_post(
    post_id: int,
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    excerpt: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    is_premium: Optional[bool] = Form(None),
    featured_image: Optional[str] = Form(None),
    seo_title: Optional[str] = Form(None),
    meta_description: Optional[str] = Form(None),
    focus_keyword: Optional[str] = Form(None),
    secondary_keywords: Optional[str] = Form(None),
    current_user: dict = Depends(get_admin_user)
):
    """Update blog post"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT * FROM blog_posts WHERE id = $1", post_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Post not found")
        
        async with conn.transaction():
            # Update post fields
            updates = []
            values = []
            
            if title:
                updates.append("title = $" + str(len(values)+1))
                values.append(title)
            if content:
                updates.append("content = $" + str(len(values)+1))
                values.append(content)
                # Recalculate reading time
                word_count = len(content.split())
                reading_time = math.ceil(word_count / 200)
                updates.append("reading_time_minutes = $" + str(len(values)+1))
                values.append(reading_time)
            if excerpt:
                updates.append("excerpt = $" + str(len(values)+1))
                values.append(excerpt)
            if category:
                updates.append("category = $" + str(len(values)+1))
                values.append(category)
            if status:
                updates.append("status = $" + str(len(values)+1))
                values.append(status)
                if status == 'published' and existing['status'] != 'published':
                    updates.append("published_at = CURRENT_TIMESTAMP")
            if is_premium is not None:
                updates.append("is_premium = $" + str(len(values)+1))
                values.append(is_premium)
            if featured_image:
                updates.append("featured_image = $" + str(len(values)+1))
                values.append(featured_image)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(post_id)
            
            if updates:
                query = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ${len(values)}"
                await conn.execute(query, *values)
            
            # Update SEO if any SEO fields provided
            if any([seo_title, meta_description, focus_keyword, secondary_keywords]):
                # Get current content for scoring if not updated
                current_content = content or existing['content']
                current_title = seo_title or title or existing['title']
                
                seo_analysis = calculate_seo_score(
                    current_content, 
                    current_title, 
                    meta_description or "", 
                    focus_keyword or ""
                )
                
                seo_updates = []
                seo_values = [post_id]
                
                if seo_title:
                    seo_updates.append("seo_title = $2")
                    seo_values.append(seo_title)
                if meta_description:
                    seo_updates.append("meta_description = $3")
                    seo_values.append(meta_description)
                if focus_keyword:
                    seo_updates.append("focus_keyword = $4")
                    seo_values.append(focus_keyword)
                if secondary_keywords:
                    seo_updates.append("secondary_keywords = $5")
                    seo_values.append(secondary_keywords.split(','))
                
                seo_updates.append(f"seo_score = ${len(seo_values)+1}")
                seo_values.append(seo_analysis['score'])
                seo_updates.append(f"keyword_density = ${len(seo_values)+1}")
                seo_values.append(seo_analysis['keyword_density'])
                seo_updates.append("updated_at = CURRENT_TIMESTAMP")
                
                await conn.execute(f"""
                    UPDATE blog_seo_data 
                    SET {', '.join(seo_updates)}
                    WHERE post_id = $1
                """, *seo_values)
        
        return await get_post(post_id, current_user)

@router.delete("/{post_id}")
async def delete_post(post_id: int, current_user: dict = Depends(get_admin_user)):
    """Delete blog post"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM blog_posts WHERE id = $1", post_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post deleted successfully"}

@router.post("/{post_id}/media")
async def add_media(
    post_id: int,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    alt_text: Optional[str] = Form(None),
    is_featured: bool = Form(False),
    current_user: dict = Depends(get_admin_user)
):
    """Add media to blog post"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Here you would typically upload to Cloudinary/S3
    # For now, placeholder local path
    file_url = f"/uploads/blog/{file.filename}"
    
    async with database.db_pool.acquire() as conn:
        max_order = await conn.fetchval("""
            SELECT COALESCE(MAX(sort_order), 0) FROM blog_media WHERE post_id = $1
        """, post_id)
        
        media_id = await conn.fetchval("""
            INSERT INTO blog_media (post_id, filename, url, caption, alt_text, sort_order, is_featured, mime_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, post_id, file.filename, file_url, caption, alt_text or caption, max_order + 1, is_featured, file.content_type)
        
        return {"id": media_id, "url": file_url, "message": "Media added successfully"}

@router.get("/{post_id}/seo-analysis")
async def analyze_post_seo(
    post_id: int,
    current_user: dict = Depends(get_admin_user)
):
    """Get detailed SEO analysis for a post"""
    if not database.db_pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    async with database.db_pool.acquire() as conn:
        post = await conn.fetchrow("""
            SELECT b.title, b.content, bd.seo_title, bd.meta_description, bd.focus_keyword
            FROM blog_posts b
            LEFT JOIN blog_seo_data bd ON b.id = bd.post_id
            WHERE b.id = $1
        """, post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        analysis = calculate_seo_score(
            post['content'],
            post['seo_title'] or post['title'],
            post['meta_description'] or "",
            post['focus_keyword'] or ""
        )
        
        return analysis
