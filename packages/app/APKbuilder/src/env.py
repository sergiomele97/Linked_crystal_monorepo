import os
from dotenv import load_dotenv

load_dotenv()  

ENV = os.getenv("ENV", "local")
URL = os.getenv("URL", "http://localhost:8080")
STATIC_TOKEN = os.getenv("STATIC_TOKEN", "demo_token")