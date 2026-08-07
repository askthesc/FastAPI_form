from typing import Annotated, Optional
from fastapi import FastAPI, Form, BackgroundTasks
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os
from sqlmodel import SQLModel, Field, create_engine, Session
import resend




app = FastAPI()

env = load_dotenv()
resend.api_key = os.environ['RESEND_API_KEY']
engine = create_engine(os.environ['DATABASE_URL'])



class SubmissionDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str

SQLModel.metadata.create_all(engine)

class Submission(BaseModel):
    name:str
    email: EmailStr

def save_submission(name: str, email:str):
    with Session(engine) as session:
        row = SubmissionDB(name=name, email=email)
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


@app.post("/submit")
def submit(data: Annotated[Submission, Form()], background_tasks: BackgroundTasks):
    save_submission(data.name, data.email)
    background_tasks.add_task(send_email, data.name, data.email)

    return {"status": "received"}


