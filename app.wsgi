import sys
import os

# Add your project directory to the sys.path
project_home = '/home/isaiahcreagh/repositories/line-card-generator'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import the FastAPI app and wrap it with WSGI middleware
from app import app
from asgi2wsgi import ASGI2WSGI

application = ASGI2WSGI(app)
