from sqlalchemy import Column, Integer, String, DateTime, func, Table, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base 

problemset_problem_association = Table(
    'problemset_problem_association', Base.metadata,
    Column('problemset_id', Integer, ForeignKey('problemsets.id'), primary_key=True),
    Column('problem_id', Integer, ForeignKey('problems.id'), primary_key=True)
)

class Problemset(Base):
    __tablename__ = "problemsets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    group_name = Column(String(100), index=True, nullable=False) # Target student group
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String(100), index=True, nullable=False, server_default="predavanje")

    # Define relationship to Problem model via the association table
    problems = relationship(
        "Problem",
        secondary=problemset_problem_association,
        back_populates="problemsets"
    )

    def __repr__(self):
         return f"<Problemset(id={self.id}, name='{self.name}', group='{self.group_name}, type='{self.type}')>"