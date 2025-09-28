from sqlmodel import *

import os
from dotenv import load_dotenv

load_dotenv() 

POSTGRES_URL = "postgresql://postgres.xchixbtfpksowiyexmfz:srida9840411@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

engine = create_engine(POSTGRES_URL, echo=True,pool_size=5)

def get_session():
    with Session(engine) as session:
        yield session
