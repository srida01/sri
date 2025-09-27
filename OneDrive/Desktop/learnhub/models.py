from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# Junction tables for many-to-many relationships
class UserTeachSkill(SQLModel, table=True):
    """Junction table for users who can teach skills"""
    __tablename__ = "user_teach_skills"  # Fixed: double underscores
    
    user_id: int = Field(foreign_key="user.user_id", primary_key=True)
    skill_id: int = Field(foreign_key="skill.skill_id", primary_key=True)
    experience_level: Optional[str] = None  # beginner, intermediate, advanced
    years_experience: Optional[int] = None

class UserLearnSkill(SQLModel, table=True):
    """Junction table for users who want to learn skills"""
    __tablename__ = "user_learn_skills"  # Fixed: double underscores
    
    user_id: int = Field(foreign_key="user.user_id", primary_key=True)
    skill_id: int = Field(foreign_key="skill.skill_id", primary_key=True)
    proficiency_goal: Optional[str] = None  # beginner, intermediate, advanced
    priority: Optional[int] = None  # 1-5 priority level

class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str
    email: str
    aboutme: Optional[str] = None
    
    # Many-to-many relationships through junction tables
    teaching_skills: List["Skill"] = Relationship(
        back_populates="teachers",
        link_model=UserTeachSkill
    )
    learning_skills: List["Skill"] = Relationship(
        back_populates="learners", 
        link_model=UserLearnSkill
    )

class Category(SQLModel, table=True):
    category_id: Optional[int] = Field(default=None, primary_key=True)
    category_name: str
    description: Optional[str] = None
    
    # One-to-many with skills
    skills: List["Skill"] = Relationship(back_populates="category")

class Skill(SQLModel, table=True):
    skill_id: Optional[int] = Field(default=None, primary_key=True)
    skill_name: str
    description: Optional[str] = None
    category_id: int = Field(foreign_key="category.category_id")
    
    # Relationships
    category: Optional[Category] = Relationship(back_populates="skills")
    teachers: List[User] = Relationship(
        back_populates="teaching_skills",
        link_model=UserTeachSkill
    )
    learners: List[User] = Relationship(
        back_populates="learning_skills",
        link_model=UserLearnSkill
    )