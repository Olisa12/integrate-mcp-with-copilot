"""High School Management System API backed by SQLite + SQLModel."""

import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from database import Activity, Signup, Student, create_db_and_seed, engine

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)


def get_session():
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup():
    create_db_and_seed()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(session: Session = Depends(get_session)):
    activities = session.exec(select(Activity).order_by(Activity.name)).all()
    result = {}

    for activity in activities:
        participant_emails = session.exec(
            select(Student.email)
            .join(Signup, Signup.student_id == Student.id)
            .where(Signup.activity_id == activity.id)
        ).all()

        result[activity.name] = {
            "description": activity.description,
            "schedule": activity.schedule,
            "max_participants": activity.max_participants,
            "participants": participant_emails,
        }

    return result


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    session: Session = Depends(get_session),
):
    """Sign up a student for an activity"""
    activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    student = session.exec(select(Student).where(Student.email == email)).first()
    if not student:
        student = Student(email=email)
        session.add(student)
        session.flush()

    existing_signup = session.exec(
        select(Signup).where(
            Signup.activity_id == activity.id,
            Signup.student_id == student.id,
        )
    ).first()

    if existing_signup:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up",
        )

    session.add(Signup(activity_id=activity.id, student_id=student.id))
    session.commit()

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    session: Session = Depends(get_session),
):
    """Unregister a student from an activity"""
    activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    student = session.exec(select(Student).where(Student.email == email)).first()
    if not student:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity",
        )

    signup = session.exec(
        select(Signup).where(
            Signup.activity_id == activity.id,
            Signup.student_id == student.id,
        )
    ).first()

    if not signup:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity",
        )

    session.delete(signup)
    session.commit()

    return {"message": f"Unregistered {email} from {activity_name}"}
