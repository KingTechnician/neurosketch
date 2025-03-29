# Canvas Data Generation with LangChain


## Setup and Dependencies

```python
pip install langchain pydantic python-dotenv
```

Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_key_here
```

## Canvas Data Structure

We'll use Pydantic to define our canvas object structure that matches the required format:

```python
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field

class CanvasObject(BaseModel):
    """Canvas object for generating drawing data."""
    # Basic identifier
    index: int = Field(default=0, description="Unique identifier for the canvas object")
    
    # Core properties
    type: str = Field(..., description="Type of canvas object (e.g., 'rect', 'circle', 'path')")
    version: str = Field(default="5.3.0", description="Fabric.js version")
    originX: str = Field(default="left", description="Horizontal origin point")
    originY: str = Field(default="top", description="Vertical origin point")
    left: float = Field(..., description="Left position of object")
    top: float = Field(..., description="Top position of object")
    width: float = Field(..., description="Width of object")
    height: float = Field(..., description="Height of object")
    
    # Style properties
    fill: Optional[str] = Field(None, description="Fill color (e.g., '#ff0000')")
    stroke: str = Field(default="", description="Stroke color")
    strokeWidth: int = Field(default=1, description="Width of stroke")
    strokeDashArray: Optional[List[float]] = Field(None, description="Pattern of dashes and gaps")
    strokeLineCap: str = Field(default="butt", description="Style of line endings")
    strokeDashOffset: int = Field(default=0, description="Offset for dash pattern")
    strokeLineJoin: str = Field(default="miter", description="Style of line joins")
    strokeUniform: bool = Field(default=False, description="Whether stroke width is affected by zoom")
    strokeMiterLimit: int = Field(default=4, description="Limit on miter line join")
    
    # Transform properties
    scaleX: float = Field(default=1.0, description="Horizontal scale factor")
    scaleY: float = Field(default=1.0, description="Vertical scale factor")
    angle: float = Field(default=0.0, description="Rotation angle in degrees")
    flipX: bool = Field(default=False, description="Horizontal flip")
    flipY: bool = Field(default=False, description="Vertical flip")
    skewX: float = Field(default=0.0, description="Horizontal skew")
    skewY: float = Field(default=0.0, description="Vertical skew")
    
    # Appearance properties
    opacity: float = Field(default=1.0, description="Object opacity")
    visible: bool = Field(default=True, description="Object visibility")
    backgroundColor: Optional[str] = Field(None, description="Background color")
    fillRule: str = Field(default="nonzero", description="Fill rule for paths")
    paintFirst: str = Field(default="fill", description="Whether to paint fill or stroke first")
    globalCompositeOperation: str = Field(
        default="source-over", 
        description="How object should composite with objects behind it"
    )
    
    # Path data
    path: Optional[List[List[Any]]] = Field(None, description="Path data for custom shapes")
```

## LangChain Configuration

Here's how to set up LangChain to generate canvas objects:

```python
import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

# Initialize the chat model
llm = ChatOpenAI(
    model_name="gpt-4",
    temperature=0.7
)

# Create a structured output generator
canvas_generator = llm.with_structured_output(CanvasObject)

# System prompt template
system_prompt = """You are a canvas drawing assistant that generates data for drawing objects.
Follow these guidelines:
- Generate valid coordinates within a 1000x1000 canvas
- Use web color formats for colors (e.g., '#ff0000', 'blue')
- Ensure all required fields are populated
- Generate appropriate path data for custom shapes
- Keep transformations reasonable (e.g., scale between 0.1 and 2.0)
"""

# Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])

# Create the generation chain
generation_chain = prompt | canvas_generator
```

## Usage Examples

### 1. Generate a Simple Rectangle

```python
rectangle_prompt = "Create a blue rectangle near the center of the canvas"

result = generation_chain.invoke({"input": rectangle_prompt})
"""
Example output:
{
    "type": "rect",
    "left": 400,
    "top": 300,
    "width": 200,
    "height": 150,
    "fill": "#0000ff",
    "opacity": 0.8
    ...
}
"""
```

### 2. Generate a Custom Path

```python
path_prompt = "Create a zigzag line across the canvas"

result = generation_chain.invoke({"input": path_prompt})
"""
Example output:
{
    "type": "path",
    "left": 100,
    "top": 100,
    "width": 800,
    "height": 400,
    "stroke": "#000000",
    "strokeWidth": 2,
    "path": [
        ["M", 0, 0],
        ["L", 200, 100],
        ["L", 400, 0],
        ["L", 600, 100],
        ["L", 800, 0]
    ]
    ...
}
"""
```

### 3. Generate Multiple Objects

To generate multiple objects, create a list schema:

```python
from typing import List
from pydantic import BaseModel

class CanvasComposition(BaseModel):
    """A collection of canvas objects forming a composition."""
    objects: List[CanvasObject] = Field(
        ..., 
        description="List of canvas objects in the composition"
    )

# Create a new generator for compositions
composition_generator = llm.with_structured_output(CanvasComposition)

# Update the chain
composition_chain = prompt | composition_generator

# Generate a composition
composition_prompt = "Create a scene with a sun above mountains"

result = composition_chain.invoke({"input": composition_prompt})
"""
Example output:
{
    "objects": [
        {
            "type": "circle",
            "left": 500,
            "top": 100,
            "width": 100,
            "height": 100,
            "fill": "#ffdd00",
            ...
        },
        {
            "type": "path",
            "left": 200,
            "top": 300,
            "width": 600,
            "height": 300,
            "fill": "#4a5568",
            "path": [
                ["M", 0, 300],
                ["L", 200, 0],
                ["L", 400, 200],
                ["L", 600, 0],
                ["L", 600, 300],
                ["Z"]
            ],
            ...
        }
    ]
}
"""
```

## Error Handling

The structured output parser will validate all generated objects against the Pydantic model. If the LLM generates invalid data, an error will be raised. You can handle these cases with a try-except block:

```python
try:
    result = generation_chain.invoke({"input": prompt})
except ValueError as e:
    print(f"Error generating canvas data: {e}")
    # Handle the error or retry with a different prompt
```

## Best Practices

1. **Prompt Engineering**:
   - Be specific about desired positions and sizes
   - Mention color preferences explicitly
   - Describe shapes and paths clearly

2. **Validation**:
   - Always validate generated coordinates are within canvas bounds
   - Ensure color values are in valid web format
   - Verify path data follows correct structure

3. **Performance**:
   - Cache commonly used shapes or patterns
   - Batch multiple object generations when possible
   - Consider using a lower-temperature setting for more consistent results

4. **Error Recovery**:
   - Implement retry logic for failed generations
   - Have fallback shapes for complex path generations
   - Log and analyze common failure patterns

## Limitations

1. The LLM may occasionally generate:
   - Invalid color formats
   - Out-of-bounds coordinates
   - Malformed path data
   
2. Complex shapes might require multiple attempts to generate correctly

3. Generation time increases with composition complexity

## Future Improvements

1. Implement template-based generation for common shapes
2. Add support for gradients and patterns
3. Create a library of pre-validated path templates
4. Develop interactive correction mechanisms for invalid generations
