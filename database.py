from sqlmodel import SQLModel, create_engine, Field, Session

# If you have models in models.py from which you want to create
# tables, import models.py here.
import models

# Define the database file name
sqlite_filename = 'database.db'
# Create a sqlite database for development
sqlite_url = f"sqlite:///{sqlite_filename}"

# The name engine will refer to that database engine.
# echo = True is just for development, not production.
engine = create_engine(sqlite_url, echo=True)

# The database.db file won't be created until you actually execute database.py.
if __name__ == '__main__':
    # Creates database.db (if it doesn't already exist)
    SQLModel.metadata.create_all(engine)