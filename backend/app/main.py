from fastapi import FastAPI
from .routes import hello_router
from utils.db_watcher import setup_db_watcher
from dotenv import load_dotenv

import os

load_dotenv()  # Load environment variables from .env file

# Create the FastAPI application
app = FastAPI(
    title="FastAPI Starter Template",
    description="A simple FastAPI starter template for beginners",
    version="1.0.0"
)

# Include our hello world router
# This is where you would add additional routers as your API grows
app.include_router(hello_router)

# Set up database file watcher
@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    def on_db_change():
        # Handle database changes here
        # This will be called when the database file changes
        pass
    
    app.state.db_observer = setup_db_watcher(on_db_change)

@app.on_event("shutdown")
async def shutdown_event():
    # Stop the file observer when the application shuts down
    if hasattr(app.state, 'db_observer'):
        app.state.db_observer.stop()
        app.state.db_observer.join()

# If running this file directly with 'python main.py', start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
