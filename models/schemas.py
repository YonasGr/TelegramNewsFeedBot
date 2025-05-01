from pydantic import BaseModel
from datetime import datetime

class FeedItem(BaseModel):
    title: str
    url: str
    content: str
    published_at: str = ""
    source_type: str
    
    class Config:
        from_attributes = True

class SourceCreate(BaseModel):
    url: str
    type: str
