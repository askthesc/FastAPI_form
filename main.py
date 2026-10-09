import logging
import os
from datetime import date, datetime
from typing import Annotated

import resend
import resend.exceptions
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Form
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from sqlmodel import Field, Session, SQLModel, create_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



app = FastAPI()

env = load_dotenv()
resend.api_key = os.environ["RESEND_API_KEY"]
engine = create_engine(os.environ["DATABASE_URL"])
app.mount("/static", StaticFiles(directory="static"), name="static")


class SubmissionDB(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    expected_last_date: date
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = None


SQLModel.metadata.create_all(engine)


class Submission(BaseModel):
    name: str
    email: EmailStr
    expected_last_date: date
    notes: str | None = None


def save_submission(
    name: str, email: str, expected_last_date: date, notes: str | None = None
):
    with Session(engine) as session:
        row = SubmissionDB(
            name=name, email=email, expected_last_date=expected_last_date, notes=notes
        )
        session.add(row)
        session.commit()


def send_email(name: str, email: str):
    try:
        resend.Emails.send(
            {
                "from": "onboarding@resend.dev",
                "to": "askthesc@gmail.com",
                "subject": "Hello",
                "html": "<p>just saying hi</p>",
            }
        )
    except resend.exceptions.ResendError as e:
        logger.error(f"Failed to send email to {email}: {e}")
    # print(f"pretending to email {name} at {email}")


@app.get("/thank-you")
def thank_you_page():
    return FileResponse("static/thank_you.html")


@app.post("/submit")
def submit(data: Annotated[Submission, Form()], background_tasks: BackgroundTasks):
    save_submission(data.name, data.email, data.expected_last_date, data.notes)
    background_tasks.add_task(send_email, data.name, data.email)

    return RedirectResponse(url="/thank-you", status_code=303)


@app.get("/")
def form_page():
    return FileResponse("static/index.html")
