from pydantic import BaseModel

class AdminCreate(BaseModel):
    username: str
    password: str

class Admin(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True
