import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_URL = os.getenv("CLIENT_URL", "http://localhost:3000")
