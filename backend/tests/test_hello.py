from fastapi.testclient import TestClient
from app.main import app

# Create a test client using our FastAPI application
client = TestClient(app)

def test_hello_world():
    """
    Test the root endpoint (/) to ensure it:
    1. Returns a 200 status code
    2. Returns JSON with the expected hello world message
    3. Matches our HelloWorldResponse schema
    """
    # Make a GET request to the root endpoint
    response = client.get("/")
    
    # Check that the response has a 200 (OK) status code
    assert response.status_code == 200
    
    # Check that the response JSON contains our expected message
    data = response.json()
    assert data == {"message": "Hello, World!"}
