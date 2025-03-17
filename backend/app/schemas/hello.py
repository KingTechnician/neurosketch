from pydantic import BaseModel

# Schema for the Hello World request
# Currently empty as we don't need any input parameters for this simple endpoint
class HelloWorldRequest(BaseModel):
    pass

# Schema for the Hello World response
# Defines the structure of our API response
class HelloWorldResponse(BaseModel):
    message: str
