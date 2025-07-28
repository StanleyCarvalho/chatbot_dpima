import sys
import os

sys.path.insert(0, "/var/www/chatbot-dpima")
os.chdir("/var/www/chatbot-dpima")

from app import app as application
