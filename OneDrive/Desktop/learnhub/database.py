from sqlmodel import *

import os
from dotenv import load_dotenv

load_dotenv() 

POSTGRES_URL = os.environ["database_url"]

engine = create_engine(POSTGRES_URL, echo=True,pool_size=5)

def get_session():
    with Session(engine) as session:
        yield session
