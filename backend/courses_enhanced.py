from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, update, func
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime

from .database import database, courses, course_quizzes, user_progress
from .security import get_current_user, get_current_admin

router = APIRouter(prefix="/courses", tags=["courses_enhanced"])

class QuizCreate(BaseModel):
    title: str
    questions: List[Dict]
    passing_score: int = Field(70, ge=0, le=100)

class QuizSubmission(BaseModel):
    quiz_id: int
    answers: Dict[int, str]

@router.post("/{course_id}/quizzes")
async def add_quiz(
    course_id: int,
    quiz_data: QuizCreate,
    current_user: dict = Depends(get_current_admin)
):
    query = insert(course_quizzes).values(
        course_id=course_id,
        title=quiz_data.title,
        questions=quiz_data.questions,
        passing_score=quiz_data.passing_score,
        order_index=0
    )
    quiz_id = await database.execute(query)
    return {"id": quiz_id, "message": "Quiz added"}

@router.post("/{course_id}/quizzes/{quiz_id}/submit")
async def submit_quiz(
    course_id: int,
    quiz_id: int,
    submission: QuizSubmission,
    current_user: dict = Depends(get_current_user)
):
    query = select(course_quizzes).where(course_quizzes.c.id == quiz_id)
    quiz = await database.fetch_one(query)

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    correct_count = 0
    total_questions = len(quiz["questions"])
    results = []

    for idx, question in enumerate(quiz["questions"]):
        user_answer = submission.answers.get(str(idx))
        is_correct = user_answer == question["correct_answer"]
        if is_correct:
            correct_count += 1

        results.append({
            "question": question["question"],
            "your_answer": user_answer,
            "correct_answer": question["correct_answer"],
            "is_correct": is_correct,
            "explanation": question.get("explanation", "")
        })

    score = (correct_count / total_questions) * 100
    passed = score >= quiz["passing_score"]

    query = select(user_progress).where(
        (user_progress.c.user_id == current_user["id"]) &
        (user_progress.c.course_id == course_id)
    )
    existing = await database.fetch_one(query)

    quiz_scores = {str(quiz_id): score}

    if existing:
        existing_scores = existing["quiz_scores"] or {}
        existing_scores.update(quiz_scores)

        total_quizzes_query = select(func.count()).where(course_quizzes.c.course_id == course_id)
        total_quizzes = await database.fetch_val(total_quizzes_query)

        completed_quizzes = len(existing_scores)
        overall = (completed_quizzes / total_quizzes) * 100 if total_quizzes > 0 else 0

        query = update(user_progress).where(user_progress.c.id == existing["id"]).values(
            quiz_scores=existing_scores,
            overall_progress=min(100, overall),
            completed_at=datetime.utcnow() if overall >= 100 else None
        )
    else:
        query = insert(user_progress).values(
            user_id=current_user["id"],
            course_id=course_id,
            quiz_scores=quiz_scores,
            overall_progress=0,
            completed_lessons=[]
        )

    await database.execute(query)

    return {
        "score": round(score, 1),
        "passed": passed,
        "correct_answers": correct_count,
        "total_questions": total_questions,
        "results": results
    }

@router.get("/my-progress")
async def get_my_progress(current_user: dict = Depends(get_current_user)):
    query = select(
        user_progress,
        courses.c.title,
        courses.c.id.label("course_id")
    ).join(courses).where(user_progress.c.user_id == current_user["id"])

    results = await database.fetch_all(query)
    return [dict(r) for r in results]
