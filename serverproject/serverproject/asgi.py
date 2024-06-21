"""
ASGI config for serverproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

# import os
# from django.core.asgi import get_asgi_application
# from starlette.staticfiles import StaticFiles
# from starlette.applications import Starlette
# from pathlib import Path

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverproject.settings')

# BASE_DIR = Path(__file__).resolve().parent.parent

# # Initialize Django ASGI application early to ensure the Django settings are loaded
# django_asgi_app = get_asgi_application()

# # Check if static path exists
# static_path = os.path.join(BASE_DIR, "destinyapp/static")
# print(f"Static path exists: {os.path.exists(static_path)}")

# # Create a Starlette application to serve static files
# app = Starlette(debug=True)
# app.mount('/static', StaticFiles(directory=static_path), name='static')

# # The Django ASGI app should be the default to handle all non-static requests
# application = django_asgi_app


import os
from django.core.asgi import get_asgi_application
from starlette.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.routing import Mount
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'serverproject.settings')

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize Django ASGI application to ensure the Django settings are loaded
django_asgi_app = get_asgi_application()

# Define the list of middleware
middleware = [
    Middleware(TrustedHostMiddleware, allowed_hosts=['*']),
]

# Create the Starlette application instance with middleware and routes
app = Starlette(debug=True, middleware=middleware)

# Add the Django ASGI app as a fallback for any non-static file requests
app.mount('', django_asgi_app)

# The 'application' is what Uvicorn will look for by default
application = app


