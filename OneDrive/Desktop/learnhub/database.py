from sqlmodel import *

import os
from dotenv import load_dotenv

load_dotenv() 

POSTGRES_URL = "postgresql://postgres:srida9840411@db.xchixbtfpksowiyexmfz.supabase.co:5432/postgres"

engine = create_engine(POSTGRES_URL, echo=True,pool_size=5)

def get_session():
    with Session(engine) as session:
        yield session
