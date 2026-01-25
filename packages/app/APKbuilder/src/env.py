# Valores por defecto
ENV = "local"
URL = "http://localhost:8080"
SSL_URL = ""
STATIC_TOKEN = "demo_token"
PORT = "8080"
SERVERS = "localhost"

try:
    from config import ENV, URL, SSL_URL, STATIC_TOKEN, PORT, SERVERS
    ENV = ENV
    URL = URL
    SSL_URL = SSL_URL
    STATIC_TOKEN = STATIC_TOKEN
    PORT = PORT
    SERVERS = SERVERS
except ImportError:
    print("config.py no encontrado, usando valores por defecto")
