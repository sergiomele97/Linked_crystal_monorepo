import os

with open("config.py", "w") as f:
    f.write(f'ENV = "{os.getenv("ENV", "local")}"\n')
    f.write(f'URL = "{os.getenv("URL", "http://localhost:8080")}"\n')
    f.write(f'STATIC_TOKEN = "{os.getenv("STATIC_TOKEN", "demo_token")}"\n')
    f.write(f'PORT = "{os.getenv("PORT", "8080")}"\n')
    f.write(f'SERVERS = "{os.getenv("SERVERS", "localhost")}"\n')