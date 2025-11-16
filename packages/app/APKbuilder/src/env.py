import os
from dotenv import load_dotenv

load_dotenv()  

ENV = os.getenv("ENV")
URL = os.getenv("URL")
STATIC_TOKEN = os.getenv("STATIC_TOKEN")