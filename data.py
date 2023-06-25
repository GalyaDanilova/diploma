# импорт

import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from config import db_url_object

metadata = MetaData()
Base = declarative_base()

engine = create_engine(db_url_object)

"""CREATE DATABASE student_diplom
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Russian_Russia.1251'
    LC_CTYPE = 'Russian_Russia.1251'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;
"""
class Viewed(Base):
    __tablename__ = 'viewed'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)


"""CREATE TABLE IF NOT EXISTS public.viewed
(
    profile_id integer NOT NULL,
    worksheet_id integer NOT NULL,
    CONSTRAINT viewed_pkey PRIMARY KEY (profile_id, worksheet_id)
)
"""


# добавление записи в бд


def add_user(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        to_bd = Viewed(profile_id=profile_id, worksheet_id=worksheet_id)
        session.add(to_bd)
        session.commit()


"""INSERT INTO public.viewed (profile_id, worksheet_id)
   VALUES (1, 123);
"""


# извлечение записей из БД

def check_user(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        from_bd = session.query(Viewed).filter(
            Viewed.profile_id == profile_id,
            Viewed.worksheet_id == worksheet_id
        ).first()
        return True if from_bd else False


"""-- Извлечение всех данных из таблицы viewed
SELECT * FROM public.viewed;
-- Извлечение данных только для определенного профиля
SELECT * FROM public.viewed WHERE profile_id = 123;
-- Извлечение данных только для определенного worksheet_id
SELECT * FROM public.viewed WHERE worksheet_id = 456;
"""

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    # add_user(engine, 2113, 124512)
    res = check_user(engine, 2113, 1245121)
    print(res)