import os
from dotenv import load_dotenv


load_dotenv()
POSTGRES_URL = os.getenv("POSTGRES_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
