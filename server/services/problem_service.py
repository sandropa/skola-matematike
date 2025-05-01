from sqlalchemy.orm import Session
from ..models.problem import Problem as DBProblem 
from ..schemas.problem import ProblemSchema  

def get_all(db: Session):
    return db.query(DBProblem).all()

def get_one(db: Session, problem_id: int):
    return db.query(DBProblem).filter(DBProblem.id == problem_id).first()

def create(db: Session, problem: ProblemSchema):
    db_problem = DBProblem(**problem.dict())
    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem

def update(db: Session, problem_id: int, new_problem: ProblemSchema):
    db_problem = db.query(DBProblem).filter(DBProblem.id == problem_id).first()
    if not db_problem:
        return None
    
    for key, value in new_problem.dict().items():
        setattr(db_problem, key, value)

    db.commit()
    db.refresh(db_problem)
    return db_problem

def delete(db: Session, problem_id: int):
    db_problem = db.query(DBProblem).filter(DBProblem.id == problem_id).first()
    if not db_problem:
        return False
    
    db.delete(db_problem)
    db.commit()
    return True
