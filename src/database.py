"""Database models and helpers for the activities API."""

from pathlib import Path
from typing import Optional

from sqlmodel import Field, Session, SQLModel, UniqueConstraint, create_engine, select

SQLITE_FILE = Path(__file__).parent / "activities.db"
DATABASE_URL = f"sqlite:///{SQLITE_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str
    schedule: str
    max_participants: int


class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: Optional[str] = None
    grade_level: Optional[str] = None


class Signup(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("activity_id", "student_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="activity.id")
    student_id: int = Field(foreign_key="student.id")


SEED_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


def _get_or_create_student(session: Session, email: str) -> Student:
    student = session.exec(select(Student).where(Student.email == email)).first()
    if student:
        return student

    student = Student(email=email)
    session.add(student)
    session.flush()
    return student


def create_db_and_seed() -> None:
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        has_data = session.exec(select(Activity.id)).first()
        if has_data:
            return

        for name, details in SEED_ACTIVITIES.items():
            activity = Activity(
                name=name,
                description=details["description"],
                schedule=details["schedule"],
                max_participants=details["max_participants"],
            )
            session.add(activity)
            session.flush()

            for email in details["participants"]:
                student = _get_or_create_student(session, email)
                session.add(Signup(activity_id=activity.id, student_id=student.id))

        session.commit()
