from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

# VideoBase (main user fields for Video table)
class VideoBase(SQLModel):
    title: str = Field(min_length=1,max_length=128,index=True)
    youtube_code: str = Field(regex='[^ ]{11}')
    # Link to Category model
    category_id: int = Field(foreign_key='category.id')

# Video class and sql table (includes VideoBase attributes)
class Video(VideoBase, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    # is_active is True (1) for normal rows, False (0) for deleted rows
    is_active: bool = Field(default=True)
    # Date this row was created, defaults to utc now
    date_created: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # Date this row was last changed, defaults to None
    date_last_changed: Optional[datetime] = Field(default=None, nullable=True)

# CategoryBase class (no SQL table)
class CategoryBase(SQLModel):
    name: str = Field(min_length=3, max_length=15, index=True)

# Category class (and SQL table) inherits from CategoryBase
class Category(CategoryBase, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)

# CategorizedVideos class is just for reading from joined tables
class CategorizedVideos(SQLModel):
    id: int
    category: str
    title: str
    youtube_code: str