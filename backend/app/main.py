from fastapi import FastAPI
from .routes import hello_router

# Create the FastAPI application
app = FastAPI(
    title="FastAPI Starter Template",
    description="A simple FastAPI starter template for beginners",
    version="1.0.0"
)

# Include our hello world router
# This is where you would add additional routers as your API grows
app.include_router(hello_router)

# If running this file directly with 'python main.py', start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
