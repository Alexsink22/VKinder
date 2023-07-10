import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from config import db_url_object

Base = declarative_base()

class User_data(Base):
    __tablename__ = 'user_data'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)

engine = create_engine(db_url_object)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def add_to_db(profile_id, worksheet_id):
    with Session() as session:
        to_db = User_data(profile_id=profile_id, worksheet_id=worksheet_id)
        session.add(to_db)
        session.commit()

def get_from_db(profile_id):
    with Session() as session:
        from_db = session.query(User_data.worksheet_id).filter(User_data.profile_id == profile_id).all()
        return [item[0] for item in from_db]
