from app import create_app
import os

app = create_app('config.' + os.environ['APP_CONFIG'])
