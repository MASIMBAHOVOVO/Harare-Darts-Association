"""Run the HDA Flask application locally."""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # For development with better concurrency, use threaded mode
    # For production, use a WSGI server like Gunicorn (see DEPLOYMENT.md)
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # threaded=True allows Flask to handle multiple concurrent requests
    # This improves performance significantly compared to threadless mode
    app.run(
        debug=debug_mode,
        port=5000,
        threaded=True,  # Enable threading to handle ~50 concurrent requests
        use_reloader=debug_mode,  # Auto-reload on code changes in debug mode
    )
