from typing import Annotated, Optional
from fastapi import FastAPI, Form, BackgroundTasks
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os
from sqlmodel import SQLModel, Field, create_engine, Session
import resend
from fastapi.responses import FileResponse, RedirectResponse
from datetime import date
from datetime import datetime


app = FastAPI()

env = load_dotenv()
resend.api_key = os.environ['RESEND_API_KEY']
engine = create_engine(os.environ['DATABASE_URL'])



class SubmissionDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    expected_last_date: date
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

SQLModel.metadata.create_all(engine)

class Submission(BaseModel):
    name:str
    email: EmailStr
    expected_last_date: date
    notes: Optional[str] = None

def save_submission(name: str, email:str, expected_last_date: date, notes:Optional[str] = None):
    with Session(engine) as session:
        row = SubmissionDB(name=name, email=email, expected_last_date=expected_last_date, notes=notes)
        session.add(row)
        session.commit()

def send_email(name:str, email:str):
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": "askthesc@gmail.com",
            "subject": "Hello",
            "html": "<p>just saying hi</p>",


        })
    except Exception as e:
        print(e)
    #print(f"pretending to email {name} at {email}")



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




