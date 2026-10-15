import os
import logging
from flask import Flask, render_template
from config import Config
from database.db import get_active_engine
from services.auth_service import get_current_user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('courseconnect')

def create_app(config_class=Config):
    """Application factory for CourseConnect."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure instance and database directories exist
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)

    # Register Blueprints
    from blueprints.auth_routes import auth_bp
    from blueprints.course_routes import course_bp
    from blueprints.student_routes import student_bp
    from blueprints.admin_routes import admin_bp
    from blueprints.api_routes import api_bp

    app.register_blueprint(course_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Global context processors for templates
    @app.context_processor
    def inject_global_template_vars():
        return {
            'current_user': get_current_user(),
            'db_engine': get_active_engine(),
            'app_name': 'CourseConnect'
        }

    # Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', message="The page you are looking for does not exist or has been moved."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Internal server error: {e}")
        return render_template('500.html', message="An internal database or server error occurred. Please try again later."), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[*] Starting CourseConnect application on http://127.0.0.1:{port}")
    print(f"[*] Active database engine: {get_active_engine().upper()}")
    app.run(host='0.0.0.0', port=port, debug=True)
