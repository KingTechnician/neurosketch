from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
import json
import ast


@dataclass
class CanvasObject:
    """
    Dataclass to represent canvas objects from database/JSON payload.
    Uses type hints for validation and proper parsing of the data.
    """
    # Basic identifier (unnamed in the CSV)
    index: int = 0
    
    # Core properties
    type: str = ""
    version: str = ""
    originX: str = "left"
    originY: str = "top"
    left: float = 0.0
    top: float = 0.0
    width: float = 0.0
    height: float = 0.0
    
    # Style properties
    fill: Optional[str] = None
    stroke: str = ""
    strokeWidth: int = 1
    strokeDashArray: Optional[List[float]] = None
    strokeLineCap: str = "butt"
    strokeDashOffset: int = 0
    strokeLineJoin: str = "miter"
    strokeUniform: bool = False
    strokeMiterLimit: int = 4
    
    # Transform properties
    scaleX: float = 1.0
    scaleY: float = 1.0
    angle: float = 0.0
    flipX: bool = False
    flipY: bool = False
    skewX: float = 0.0
    skewY: float = 0.0
    
    # Appearance properties
    opacity: float = 1.0
    shadow: Optional[Any] = None
    visible: bool = True
    backgroundColor: Optional[str] = None
    fillRule: str = "nonzero"
    paintFirst: str = "fill"
    globalCompositeOperation: str = "source-over"
    
    # Path data
    path: Optional[List[List[Any]]] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CanvasObject':
        """
        Create a CanvasObject from a dictionary (JSON data from DB).
        Handles type conversion and special fields.
        
        Args:
            data: Dictionary containing object properties
            
        Returns:
            CanvasObject: Instantiated object with proper types
        """
        # Create a copy of the data to avoid modifying the input
        processed_data = data.copy()
        
        # Handle special fields
        if "" in processed_data:  # Unnamed column (index)
            processed_data["index"] = processed_data.pop("")
            
        # Process the path string if it exists
        if "path" in processed_data and isinstance(processed_data["path"], str):
            try:
                processed_data["path"] = ast.literal_eval(processed_data["path"])
            except (SyntaxError, ValueError):
                processed_data["path"] = None
        
        # Handle None values in various formats
        for key, value in processed_data.items():
            if value == "None" or value == "null":
                processed_data[key] = None
        
        # Create the object with the processed data
        return cls(**{k: v for k, v in processed_data.items() if hasattr(cls, k)})
    
    def to_dict(self) -> dict:
        """
        Convert the object to a dictionary, suitable for JSON serialization.
        
        Returns:
            dict: Dictionary representation of the object
        """
        result = {}
        for key, value in self.__dict__.items():
            # Handle special serialization cases
            if key == "path" and value is not None:
                result[key] = str(value)
            else:
                result[key] = value
        return result

