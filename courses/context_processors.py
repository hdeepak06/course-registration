from django.conf import settings

def global_context(request):
    """Provides application-wide context to templates."""
    db_engine = getattr(settings, 'ACTIVE_DB_NAME', 'MySQL')
    return {
        'db_engine': db_engine,
        'app_name': 'CourseConnect'
    }
