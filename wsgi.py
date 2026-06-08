import sys
print("Python version:", sys.version)
print("Starting wsgi...")

try:
    from app import create_app
    print("App module imported")
    app = create_app()
    print("App created successfully")
except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
    raise

if __name__ == "__main__":
    app.run()
