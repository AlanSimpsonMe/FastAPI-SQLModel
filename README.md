# FastAPI and SQLModel
This code is taught and explained in my [Hands-On Beginner FastAPI and SQLModel](https://alansimpson.me/fastapi/) course

Make sure you're using Python 3.6 or later. In Windows you might need to execute `py -V` to get the version number. On a Mac try `python3 -V`. If they don't work, replace `py` or `python3` below with whatever does work for you. In VS Code terminal (or whatever command line you're using), follow these steps to create a virtual environment and install dependencies.

Windows
-------

`py -m venv venv`  
`venv\scripts\activate`  
`pip install -r requirements.txt`

Mac
---

`python3 -m venv venv`  
`source venv/bin/activate`  
`pip install -r requirements.txt`

When that's all done run it with the command

`uvicorn main:app --reload`

The browse to http://127.0.0.1:8000
