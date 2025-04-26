from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from typing import List, Optional, Union, Literal,Dict,Any
from pydantic import BaseModel, Field, model_validator, field_validator
import json

# Define the command models
class BasePathCommand(BaseModel):
    """Base model for all path commands."""
    command_type: Literal["M", "L", "Q", "Z"]
    
    def to_list(self) -> List:
        """Convert command to list format."""
        raise NotImplementedError("Subclasses must implement this method")

class MoveCommand(BasePathCommand):
    """Move to command (M) for canvas paths."""
    command_type: Literal["M"] = "M"
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    
    def to_list(self) -> List:
        """Convert to list format."""
        return ["M", self.x, self.y]

class LineCommand(BasePathCommand):
    """Line to command (L) for canvas paths."""
    command_type: Literal["L"] = "L"
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    
    def to_list(self) -> List:
        """Convert to list format."""
        return ["L", self.x, self.y]

class QuadraticCurveCommand(BasePathCommand):
    """Quadratic curve command (Q) for canvas paths."""
    command_type: Literal["Q"] = "Q"
    control_x: float = Field(..., description="Control point X coordinate")
    control_y: float = Field(..., description="Control point Y coordinate") 
    end_x: float = Field(..., description="End point X coordinate")
    end_y: float = Field(..., description="End point Y coordinate")
    
    def to_list(self) -> List:
        """Convert to list format."""
        return ["Q", self.control_x, self.control_y, self.end_x, self.end_y]

class ClosePathCommand(BasePathCommand):
    """Close path command (Z) for canvas paths."""
    command_type: Literal["Z"] = "Z"
    
    def to_list(self) -> List:
        """Convert to list format."""
        return ["Z"]

# Define PathCommand as a Union for validation
PathCommand = Union[MoveCommand, LineCommand, QuadraticCurveCommand, ClosePathCommand]

class Path(BaseModel):
    """Class representing a complete path with multiple commands."""
    commands: List[PathCommand] = Field(
        ..., 
        description="List of path commands (Move, Line, Quadratic, Close)",
        min_items=1  # Require at least one command
    )
    
    def to_list(self) -> List[List]:
        """Convert the path to a list of lists format for canvas rendering."""
        return [cmd.to_list() for cmd in self.commands]

class CanvasObject(BaseModel):
    """
    Model to represent canvas objects with proper validation.
    """
    # Core properties - required
    type: Literal["path", "circle", "rect", "line"] = Field(
        ..., 
        description="Type of canvas object (path, circle, rect, or line)"
    )
    left: float = Field(..., description="Left position (X coordinate)")
    top: float = Field(..., description="Top position (Y coordinate)")
    width: float = Field(
        ..., 
        gt=0,  # Must be greater than 0
        description="Width of the object (REQUIRED, must be positive)"
    )
    height: float = Field(
        ..., 
        gt=0,  # Must be greater than 0
        description="Height of the object (REQUIRED, must be positive)"
    )
    
    # Path data - required for path type
    path: Optional[Path] = Field(
        None, 
        description="Path data (required for path type objects)"
    )
    
    # Optional properties with defaults
    version: str = Field(default="4.4.0", description="Canvas object version")
    originX: Literal["left", "center", "right"] = Field(
        default="left", 
        description="Horizontal origin"
    )
    originY: Literal["top", "center", "bottom"] = Field(
        default="top", 
        description="Vertical origin"
    )
    
    # Style properties
    fill: Optional[str] = Field(
        default=None, 
        description="Fill color (e.g. '#FF0000' or 'red')"
    )
    stroke: str = Field(default="#000000", description="Stroke color")
    strokeWidth: int = Field(default=3, description="Width of stroke")
    
    # Validate that path type objects have path data
    @model_validator(mode='after')
    def validate_path_and_dimensions(self):
        if self.type == "path" and self.path is None:
            raise ValueError("Path type objects must have path data")
        
        # Double check width and height since they're critical
        if self.width is None or self.width <= 0:
            raise ValueError(f"Width must be greater than 0, got {self.width}")
        if self.height is None or self.height <= 0:
            raise ValueError(f"Height must be greater than 0, got {self.height}")
            
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary suitable for JSON serialization.
        Special handling for path data to convert to list of lists format.
        """
        # Start with the model's dict
        result = self.model_dump(exclude_none=True)
        
        # Convert Path object to list of lists if present
        if self.path is not None:
            result["path"] = self.path.to_list()
        
        return result
    
    def model_dump_json(self, **kwargs) -> str:
        """
        Override the default model_dump_json to use our custom to_dict method.
        """
        return json.dumps(self.to_dict(), **kwargs)

def setup_langchain_parser():
    """
    Set up the LangChain parser with the Pydantic model.
    
    Returns:
        tuple: (parser, format_instructions)
    """
    # Create the parser
    parser = PydanticOutputParser(pydantic_object=CanvasObject)
    
    # Get the format instructions
    format_instructions = parser.get_format_instructions()
    
    return parser, format_instructions

def create_prompt_template(format_instructions):
    """
    Create a prompt template with the format instructions.
    
    Args:
        format_instructions: The format instructions from the parser
        
    Returns:
        PromptTemplate: The prompt template
    """
    template = """
    Create a canvas object as described below.
    
    {description}

    Width of entire canvas: {width}
    Height of entire canvas: {height}
    
    IMPORTANT REQUIREMENTS:
    1. The width MUST be a positive number (greater than 0)
    2. The height MUST be a positive number (greater than 0)
    3. For path objects, you must include valid path commands
    
    {format_instructions}
    """
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["description", "width", "height"],
        partial_variables={"format_instructions": format_instructions}
    )
    
    return prompt