from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class ScheduleEntry(Base):
    __tablename__ = 'schedule_entries'
    id = Column(Integer, primary_key=True, index=True)
    cycle = Column(String, nullable=False)  # e.g. 'V ciklus', 'VI ciklus'
    row = Column(Integer, nullable=False)   # Row number in the schedule
    group = Column(String, nullable=False)  # e.g. 'Grupa A1', 'Grupa B', etc.
    date = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    lecturer = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    problemset_id = Column(Integer, ForeignKey('problemsets.id'), nullable=True)
    # Relationship to problemset
    problemset = relationship('Problemset', backref='schedule_entries') 