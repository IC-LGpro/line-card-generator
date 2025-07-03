import sys
import os

# Add your project directory to the sys.path
project_home = '/home/isaiahcreagh/repositories/line-card-generator'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable for Flask
os.environ['FLASK_APP'] = 'app.py'

# Import your application
from app import app as application  # 'app' is your Flask app object
