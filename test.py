from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from server.database import get_db
from server.routers import problems, problemsets

app = FastAPI()

app.include_router(problems.router)
app.include_router(problemsets.router)

@app.get("/")
def root():
    return {"message": "Database test server running"}
