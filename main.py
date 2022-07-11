from fastapi import FastAPI, status, Request, Form
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import SQLModel, Session, select
from models import Category, CategoryBase, Video, VideoBase, CategorizedVideos
from database import engine
from typing import List
from datetime import datetime
import uvicorn

# Define main app name and database name
app = FastAPI()
session = Session(bind=engine)

# For templating
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')


# Routes
# Root folder (home page)
@app.get('/', response_class=HTMLResponse)
async def home():
    return '''
    <h1>Hands-On FastAPI and SQLModel</h1>
    The code in this repository is from my online course titled Hands-On FastAPI and SQLModel. 
    <p>Most of the routes and functions in main.py accept JSON requests and return JSON results. Those you can test with the FastAPI Docs using the link below</p>
    <a href='http://127.0.0.1:8000/docs'>http://127.0.0.1:8000/docs</a>
    <p>Code in the Forms region of main.py uses HTML forms rather than JSON. You can try out the different forms and templates using the links below. Note the the HTML is largely unstyled (except for some basic styling in static/styles.css). That's intentional, so you can have clean HTML code to work with, and style things how you see fit.
    <p>
    <a href="http://127.0.0.1:8000/get_form_video_list">List Videos</a>
    </p>
    <p>
    <a href="http://127.0.0.1:8000/get_form_video_add">Add a Video</a>
    </p>
    '''

# region video_routes

# Get all active videos
@app.get('/video', response_model=List[Video])
async def get_all_videos():
    with Session(engine) as session:
        # Include only videos where is_active is True
        statement = select(Video).where(Video.is_active).order_by(Video.title)
        result = session.exec(statement)
        all_videos = result.all()
    return all_videos

# Get one video, but only if it's active
@app.get('/video/{video_id}', response_model=VideoBase)
async def get_a_video(video_id:int):
    # Return error if no active video with that id
    if not await is_active_video(video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No active video with that id")
    video = session.get(Video, video_id)
    return video

# Post a new video
@app.post('/video', status_code=status.HTTP_201_CREATED)
async def post_a_video(video:VideoBase):
    # Create a new video object from data passed in
    new_video = Video.from_orm(video)
    # Make sure new video has a valid video id
    if not await is_category_id(new_video.category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No such category")
    # Post the video
    with Session(engine) as session:
        session.add(new_video)
        session.commit()
        session.refresh(new_video)
    return new_video

# Update one video
@app.put('/video/{video_id}', response_model=VideoBase)
async def update_a_video(video_id:int, updated_video:VideoBase):
    # Block if original video not there or inactive
    if not await is_active_video(video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No such video")
    # Block if the new category id is no good
    if not await is_category_id(updated_video.category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "Invalid category")
    # Otherwise, update the existing video to match updated_video
    with Session(engine) as session:
        # Get current video object from table
        original_video = session.get(Video,video_id)
        # Get dictionary so we can loop through fields
        video_dict = updated_video.dict(exclude_unset=True)
        # Loop is an alternative to doing each field on a separate line
        for key,value in video_dict.items():
            setattr(original_video, key,value)
        # Loop doesn't do date last changed, so we do that here
        original_video.date_last_changed = datetime.utcnow()
        session.commit()
        # After refresh, original video is the same as updated video
        session.refresh(original_video)
    return original_video


# Delete one video by changing is_active to False
@app.delete('/video/{video_id}')
async def delete_a_video(video_id:int):
    if not await is_active_video(video_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No such video")
    with Session(engine) as session:
        # Get the video to delete
        video = session.get(Video, video_id)
        # Set is_active to False, and update date last changed
        video.is_active = False
        video.date_last_changed = datetime.utcnow()
        session.commit()
    return {'Deleted':video_id}


# Undelete one video by changing is_active to True
@app.delete('/undelete/{video_id}')
async def undelete_a_video(video_id:int):
    with Session(engine) as session:
        # Get the video to delete
        video = session.get(Video, video_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No such video")
        # Set is_active to True, and update date last changed
        video.is_active = True
        video.date_last_changed = datetime.utcnow()
        session.commit()
    return {'Restored':video_id}

# endregion

# region category_routes

# Get all categories
@app.get('/category', response_model=List[Category])
async def get_all_categories():
    with Session(engine) as session:
        statement = select(Category).order_by(Category.name)
        result = session.exec(statement)
        all_categories = result.all()
    return all_categories

# Post a new category
@app.post('/category', status_code=status.HTTP_201_CREATED)
async def post_a_category(category:CategoryBase):
    if await is_category_name(category.name):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Category name already in use")
    new_category = Category(name=category.name)
    with Session(engine) as session:
        session.add(new_category)
        session.commit()
        session.refresh(new_category)
    return new_category

# Get one category
@app.get('/category/{category_id}', response_model=Category)
async def get_a_category(category_id:int):
    with Session(engine) as session:
        #Alternative syntax when getting one row by id
        category = session.get(Category, category_id)
        # Return error if no such category
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No such category")
    return category

# Update one category
@app.put('/category/{category_id}', response_model=Category)
async def update_a_category(category_id:int, category:CategoryBase):
    if not await is_category_id(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No such category")
    with Session(engine) as session:
        # Get current category object from table
        current_category = session.get(Category, category_id)
        # Replace current category name with the one just passed in
        current_category.name = category.name
        # Put back in table with new name
        session.add(current_category)
        session.commit()
        session.refresh(current_category)
    return current_category


# Delete one category
@app.delete('/category/{category_id}')
async def delete_a_category(category_id:int):
    if not await is_category_id(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "No such category")
    # Don't allow them to delete category if it contains active videos
    if await count_videos_in_category(category_id) > 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can't delete category that contains active videos")
    with Session(engine) as session:
        # Get the category to delete
        category = session.get(Category, category_id)
        # Delete the category
        session.delete(category)
        session.commit()
    return {'Deleted':category_id}

# endregion

# region joins
@app.get('/categorized_video', response_model=List[CategorizedVideos])
async def get_categorized_videos():
    # Get all active videos, and include the category name (not the id)
    cat_vids = session.exec(
        select(Video.id, Category.name.label('category'), Video.title, Video.youtube_code).join(Category).where(Video.is_active).order_by(Category.name, Video.title)
    ).all()
    return cat_vids

# endregion

# region forms
# Send an HTML table of videos with click-to-edit icon
@app.get('/get_form_video_list', response_class=HTMLResponse)
async def get_form_video_list(request:Request):
    # Get all active videos, along with the category name
    active_videos = session.exec(
        select(
            Video.id, Video.title, Video.youtube_code, Category.name.label('category')
        ).join(Category).where(Video.is_active).order_by(Video.title)
    ).all()
    context = {'request': request, 'videos':active_videos, 'page_title':'Videos'}
    return templates.TemplateResponse('form_list_videos.html', context)

# Send empty form for entering a new video
@app.get('/get_form_video_add', response_class=HTMLResponse)
async def get_form_video_add(request:Request):
    # Get a list of categories fo the dropdown list on the form
    categories = session.exec(select(Category)).all()
    context = {'request':request, 'categories':categories, 'page_title':'Add a Video'}
    return templates.TemplateResponse('form_add_video.html', context)

# Accept data from form_video_add and add to the database
@app.post('/submit_form_video_add')
async def submit_form_video_add(title:str=Form(), youtube_code:str=Form(), category_id:str=Form()):
    new_video=Video(title=title, youtube_code=youtube_code,category_id=int(category_id))
    with Session(engine) as session:
        session.add(new_video)
        session.commit()
        session.refresh(new_video)
    # Return to videos list page after user saved new video
    response = RedirectResponse(url='/get_form_video_list', status_code=302)
    return response


# Send for editing one video
@app.get('/get_form_video_edit/{video_id}', response_class=HTMLResponse)
async def get_form_video_edit(video_id:int,request:Request):
    # Get the video to edit
    video=session.get(Video,video_id)
    # Get a list of categories fo the dropdown list on the form
    categories = session.exec(select(Category)).all()
    context = {'video':video, 'request':request, 'categories':categories, 'page_title':'Edit Video'}
    return templates.TemplateResponse('form_edit_video.html', context)    

# Save edited video, the post is required and path must be identical to get_form_video_edit (no action in form)
@app.post('/get_form_video_edit/{video_id}')
async def submit_form_video_edit(video_id:int, title:str=Form(), youtube_code:str=Form(), category_id:str=Form()): 
    updated_video=Video(id=video_id, title=title, youtube_code=youtube_code,category_id=int(category_id))
    with Session(engine) as session:
        original_video = session.get(Video,video_id)
        video_dict = updated_video.dict(exclude_unset=True)
        for key, value in video_dict.items():
            setattr(original_video,key,value)
        original_video.date_last_changed = datetime.utcnow()
        session.commit()
        session.refresh(original_video)
    # Return to videos list page after user saved new video
    response = RedirectResponse(url='/get_form_video_list', status_code=302)
    return response

# Virtually deletes video by setting is_active to false
# Called from form_edit_video.html and javascript
@app.get('/delete_form_video/{video_id}')
async def delete_form_video(video_id:int):
    with Session(engine) as session:
        original_video = session.get(Video,video_id)
        original_video.is_active = False
        original_video.date_last_changed = datetime.utcnow()
        session.commit()
    # Return to videos list page after user saved new video
    response = RedirectResponse(url='/get_form_video_list', status_code=302)
    return response
    
# endregion

# region validators

# returns True if category id exists, otherwise returns False
async def is_category_id(category_id:int):
    if not session.get(Category,category_id):
        return False
    return True
    
# returns True if category name exists, otherwise returns False
async def is_category_name(category_name:str):
    if session.exec(
            select(Category).where(Category.name == category_name)
        ).one_or_none():
        return True
    return False

# returns True if video id exists and is_active is True, otherwise returns False
async def is_active_video(video_id:int):
    if session.exec(
            # Select where video id is valid and is_active is True
            select(Video).where(Video.id == video_id).where(Video.is_active)
        ).one_or_none():
        return True
    return False

# returns the number of active videos in any given category
async def count_videos_in_category(category_id:int):
    rows=session.exec(
        select(Video.category_id).where(Video.category_id==category_id).where(Video.is_active)
    ).all()
    return len(rows)

# endregion


# For debugging with breakpoints in VS Code
if __name__ == '__main__':
    uvicorn.run(app,host='0.0.0.0', port=8000)













