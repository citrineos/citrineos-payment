from pydantic import BaseModel, ConfigDict


class OperatorBase(BaseModel):
    id: int
    name: str
    # Add other fields as needed

class OperatorCreate(OperatorBase):
    pass

class Operator(OperatorBase):
    model_config = ConfigDict(from_attributes=True)
    
