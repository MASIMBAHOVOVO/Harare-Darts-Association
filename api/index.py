"""Vercel serverless entry point."""
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Change working directory so Flask can resolve static/templates properly
os.chdir(PROJECT_ROOT)

from app import create_app

app = create_app()

# Ensure static and template folders are set to absolute paths for Vercel
app.static_folder = os.path.join(PROJECT_ROOT, 'static')
app.template_folder = os.path.join(PROJECT_ROOT, 'templates')
