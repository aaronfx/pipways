"""
Enhanced course features - FIXED progress tracking and certificates
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from .security import get_current_user, get_user_id, get_user_attr
from .database import database

router = APIRouter()

@router.get("/progress")
async def get_enhanced_progress(current_user = Depends(get_current_user)):
    """
    Get comprehensive learning progress including certificates.
    FIXED: Proper SQL joins and null handling.
    """
    try:
        user_id = get_user_id(current_user)
        
        query = """
            SELECT 
                c.id as course_id,
                c.title,
                c.thumbnail,
                COUNT(DISTINCT l.id) as total_lessons,
                COALESCE(up.progress_percent, 0) as progress_percent,
                COALESCE(up.completed_lessons, 0) as completed_lessons,
                up.completed_at,
                up.last_accessed,
                cert.certificate_number,
                cert.issued_at as cert_date
            FROM courses c
            LEFT JOIN course_modules m ON m.course_id = c.id
            LEFT JOIN lessons l ON l.module_id = m.id
            LEFT JOIN user_progress up ON up.course_id = c.id AND up.user_id = :user_id
            LEFT JOIN certificates cert ON cert.course_id = c.id AND cert.user_id = :user_id
            WHERE c.is_active = TRUE OR c.is_published = TRUE
            GROUP BY c.id, c.title, c.thumbnail, up.progress_percent, up.completed_lessons, 
                     up.completed_at, up.last_accessed, cert.certificate_number, cert.issued_at
            ORDER BY up.last_accessed DESC NULLS LAST
        """
        
        rows = await database.fetch_all(query, {"user_id": user_id})
        
        courses_in_progress = []
        completed_courses = []
        certificates = []
        
        for row in rows:
            total_lessons = row.get("total_lessons", 0)
            completed = row.get("completed_lessons", 0)
            progress = row.get("progress_percent", 0)
            
            course_data = {
                "course_id": row["course_id"],
                "title": row["title"],
                "thumbnail": row.get("thumbnail", ""),
                "progress_percent": progress,
                "completed_lessons": completed,
                "total_lessons": total_lessons,
                "last_accessed": row.get("last_accessed").isoformat() if row.get("last_accessed") else None,
            }
            
            if progress == 100 and row.get("completed_at"):
                completed_courses.append(course_data)
                
                if row.get("certificate_number"):
                    certificates.append({
                        "course_id": row["course_id"],
                        "course_title": row["title"],
                        "certificate_id": row["certificate_number"],
                        "issued_at": row.get("cert_date").isoformat() if row.get("cert_date") else None
                    })
            elif progress > 0:
                courses_in_progress.append(course_data)
        
        # Calculate overall stats
        total_enrolled = len(rows)
        avg_progress = sum(r.get("progress_percent", 0) for r in rows) / total_enrolled if total_enrolled > 0 else 0
        
        return {
            "user_id": user_id,
            "courses_in_progress": courses_in_progress,
            "completed_courses": completed_courses,
            "certificates_earned": certificates,
            "overall_progress_percent": round(avg_progress, 1),
            "total_courses_available": total_enrolled,
            "completed_count": len(completed_courses),
            "in_progress_count": len(courses_in_progress)
        }
        
    except Exception as e:
        print(f"[ENHANCED PROGRESS ERROR] {e}", flush=True)
        return {
            "courses_in_progress": [],
            "completed_courses": [],
            "certificates_earned": [],
            "overall_progress_percent": 0,
            "error": str(e)
        }

@router.get("/certificate/{course_id}")
async def get_certificate_detail(course_id: int, current_user = Depends(get_current_user)):
    """
    Get detailed certificate information for a specific course.
    """
    try:
        user_id = get_user_id(current_user)
        
        query = """
            SELECT 
                cert.certificate_number,
                cert.issued_at,
                c.title as course_title,
                c.description,
                u.full_name,
                u.email
            FROM certificates cert
            JOIN courses c ON cert.course_id = c.id
            JOIN users u ON cert.user_id = u.id
            WHERE cert.user_id = :uid AND cert.course_id = :cid
        """
        
        cert = await database.fetch_one(query, {"uid": user_id, "cid": course_id})
        
        if not cert:
            raise HTTPException(404, "Certificate not found. Complete the course to earn one.")
        
        return {
            "certificate_id": cert["certificate_number"],
            "recipient_name": cert["full_name"] or cert["email"].split("@")[0],
            "course_name": cert["course_title"],
            "course_description": cert["description"],
            "issue_date": cert["issued_at"].isoformat() if cert["issued_at"] else None,
            "verification_url": f"/api/courses/enhanced/verify/{cert['certificate_number']}",
            "skills_earned": ["Technical Analysis", "Risk Management", "Trading Strategy"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CERTIFICATE ERROR] {e}", flush=True)
        raise HTTPException(500, "Failed to retrieve certificate")
