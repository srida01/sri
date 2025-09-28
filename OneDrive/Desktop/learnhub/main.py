from fastapi import FastAPI,Response
from sqlmodel import *
from database import engine
from contextlib import asynccontextmanager
from models import User, Category, Skill, UserTeachSkill, UserLearnSkill

from database import get_session
from fastapi import HTTPException
from typing import Optional
from fastapi import Depends, status
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()


allow_origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

class ChatRequest(BaseModel):
    query: str


# Fixed Pydantic models
class UserCreate(SQLModel):
    username: str
    password: str
    email: str
    aboutme: Optional[str] = None

class UserRead(SQLModel):
    user_id: int
    username: str
    email: str
    aboutme: Optional[str] = None
    # Don't include password in read model for security

class CategoryCreate(SQLModel):
    category_name: str
    description: Optional[str] = None

class SkillCreate(SQLModel):
    skill_name: str
    description: Optional[str] = None
    category_id: int

class UserLearnSkillCreate(SQLModel):
    user_id: int
    skill_id: int
    proficiency_goal: Optional[str] = None
    priority: Optional[int] = None

class UserTeachSkillCreate(SQLModel):
    user_id: int
    skill_id: int
    experience_level: Optional[str] = None
    years_experience: Optional[int] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield



@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Fixed user creation endpoint
@app.post("/users/", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(**user.model_dump())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Fixed category endpoint
@app.post("/categories/", status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, session: Session = Depends(get_session)):
    db_category = Category(**category.model_dump())
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

@app.get("/category/{category_id}")
async def get_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get unique skill names from the category
    unique_skill_names = list(set([skill.skill_name for skill in category.skills]))
    
    return {
        "category": category,
        "unique_skills": unique_skill_names
    }

# Fixed skill creation
@app.post("/category/{category_id}/skills", status_code=status.HTTP_201_CREATED)
def create_skill(category_id: int, skill: SkillCreate, session: Session = Depends(get_session)):
    # Verify category exists
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Ensure skill belongs to the correct category
    skill_data = skill.model_dump()
    skill_data["category_id"] = category_id
    
    db_skill = Skill(**skill_data)
    session.add(db_skill)
    session.commit()
    session.refresh(db_skill)
    return db_skill

@app.get("/category/{category_id}/skills/{skill_id}")
async def get_skill(category_id: int, skill_id: int, session: Session = Depends(get_session)):
    skill = session.exec(
        select(Skill).where(
            Skill.skill_id == skill_id,
            Skill.category_id == category_id
        )
    ).first()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found in this category")
    return skill

# Add user to learn a skill
@app.post("/users/{user_id}/learn-skill")
async def add_learn_skill(
    user_id: int,
    learn_skill: UserLearnSkillCreate,
    session: Session = Depends(get_session)
):
    # Verify user and skill exist
    user = session.get(User, user_id)
    skill = session.get(Skill, learn_skill.skill_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if relationship already exists
    existing = session.exec(
        select(UserLearnSkill).where(
            UserLearnSkill.user_id == user_id,
            UserLearnSkill.skill_id == learn_skill.skill_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already learning this skill")
    
    # Create the relationship
    learn_skill.user_id = user_id  # Ensure correct user_id
    db_learn = UserLearnSkill(**learn_skill.model_dump())
    session.add(db_learn)
    session.commit()
    session.refresh(db_learn)
    return {"message": "Successfully added skill to learning list"}

# Add user to teach a skill
@app.post("/users/{user_id}/teach-skill")
async def add_teach_skill(
    user_id: int,
    teach_skill: UserTeachSkillCreate,
    session: Session = Depends(get_session)
):
    # Verify user and skill exist
    user = session.get(User, user_id)
    skill = session.get(Skill, teach_skill.skill_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Check if relationship already exists
    existing = session.exec(
        select(UserTeachSkill).where(
            UserTeachSkill.user_id == user_id,
            UserTeachSkill.skill_id == teach_skill.skill_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already teaching this skill")
    
    # Create the relationship
    teach_skill.user_id = user_id  # Ensure correct user_id
    db_teach = UserTeachSkill(**teach_skill.model_dump())
    session.add(db_teach)
    session.commit()
    session.refresh(db_teach)
    return {"message": "Successfully added skill to teaching list"}

# Get all users learning a specific skill
@app.get("/category/{category_id}/skills/{skill_id}/learners")
async def get_skill_learners(
    category_id: int, 
    skill_id: int,
    session: Session = Depends(get_session)
):
    skill = session.exec(
        select(Skill).where(
            Skill.skill_id == skill_id,
            Skill.category_id == category_id
        )
    ).first()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    # Get learners with their learning details
    learners_data = session.exec(
        select(User, UserLearnSkill)
        .join(UserLearnSkill, User.user_id == UserLearnSkill.user_id)
        .where(UserLearnSkill.skill_id == skill_id)
    ).all()
    
    return {
        "skill": skill,
        "learners_count": len(learners_data),
        "learners": [
            {
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "aboutme": user.aboutme
                },
                "proficiency_goal": learn_data.proficiency_goal,
                "priority": learn_data.priority
            }
            for user, learn_data in learners_data
        ]
    }

# Get all users teaching a specific skill
@app.get("/category/{category_id}/skills/{skill_id}/teachers")
async def get_skill_teachers(
    category_id: int, 
    skill_id: int,
    session: Session = Depends(get_session)
):
    skill = session.exec(
        select(Skill).where(
            Skill.skill_id == skill_id,
            Skill.category_id == category_id
        )
    ).first()
    
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    teachers_data = session.exec(
        select(User, UserTeachSkill)
        .join(UserTeachSkill, User.user_id == UserTeachSkill.user_id)
        .where(UserTeachSkill.skill_id == skill_id)
    ).all()
    
    return {
        "skill": skill,
        "teachers_count": len(teachers_data),
        "teachers": [
            {
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "aboutme": user.aboutme
                },
                "experience_level": teach_data.experience_level,
                "years_experience": teach_data.years_experience
            }
            for user, teach_data in teachers_data
        ]
    }

# Get user's learning skills
@app.get("/users/{user_id}/learning-skills")
async def get_user_learning_skills(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    learning_data = session.exec(
        select(Skill, UserLearnSkill)
        .join(UserLearnSkill, Skill.skill_id == UserLearnSkill.skill_id)
        .where(UserLearnSkill.user_id == user_id)
    ).all()
    
    return {
        "user_id": user_id,
        "learning_skills": [
            {
                "skill": skill,
                "proficiency_goal": learn_data.proficiency_goal,
                "priority": learn_data.priority
            }
            for skill, learn_data in learning_data
        ]
    }

# Get user's teaching skills
@app.get("/users/{user_id}/teaching-skills")
async def get_user_teaching_skills(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    teaching_data = session.exec(
        select(Skill, UserTeachSkill)
        .join(UserTeachSkill, Skill.skill_id == UserTeachSkill.skill_id)
        .where(UserTeachSkill.user_id == user_id)
    ).all()
    
    return {
        "user_id": user_id,
        "teaching_skills": [
            {
                "skill": skill,
                "experience_level": teach_data.experience_level,
                "years_experience": teach_data.years_experience
            }
            for skill, teach_data in teaching_data
        ]
    }
@app.post("/chat")
async def chat_response(request: ChatRequest):
    
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": request.query}]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(GEMINI_API_URL, headers=headers, json=body)
            response.raise_for_status()
        data = response.json()
        ai_response = "".join(part.get("text", "") for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []))
        return {"response": ai_response}
    except httpx.ReadTimeout:
        return {"response": "Request timed out. Please try again later."}
    except httpx.HTTPStatusError as e:
        return {"response": f"API error: {e.response.text}"}
    except Exception as e:
        return {"response": f"An unexpected error occurred: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

