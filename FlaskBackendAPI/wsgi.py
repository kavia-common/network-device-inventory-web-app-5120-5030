from app import create_app

# PUBLIC_INTERFACE
def application():
    """WSGI entrypoint for servers expecting 'application' callable."""
    return create_app()
