from kivy.utils import platform

# Valores por defecto
ENV = "local"
URL = "http://localhost:8080"
SSL_URL = ""
STATIC_TOKEN = "demo_token"
PORT = "8080"
SERVERS = "localhost"

if platform != "android":
    # Desktop: cargar .env si existe
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        ENV = os.getenv("ENV", ENV)
        URL = os.getenv("URL", URL)
        SSL_URL = os.getenv("SSL_URL", SSL_URL)
        STATIC_TOKEN = os.getenv("STATIC_TOKEN", STATIC_TOKEN)
        PORT = os.getenv("PORT", PORT)
        SERVERS = os.getenv("SERVERS", SERVERS)
    except ImportError:
        print("python-dotenv no instalado, usando valores por defecto")
else:
    # Android: importar config.py generado dinámicamente
    try:
        from config import ENV as cfg_ENV, URL as cfg_URL, SSL_URL as cfg_SSL_URL, STATIC_TOKEN as cfg_STATIC_TOKEN, PORT as cfg_PORT, SERVERS as cfg_SERVERS
        ENV = cfg_ENV
        URL = cfg_URL
        SSL_URL = cfg_SSL_URL
        STATIC_TOKEN = cfg_STATIC_TOKEN
        PORT = cfg_PORT
        SERVERS = cfg_SERVERS
    except ImportError:
        print("config.py no encontrado, usando valores por defecto")
