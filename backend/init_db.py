"""
Initialize the database — creates all tables.
Run once before starting the server: python init_db.py
"""
from database import Base, engine

def init():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. Tables created: interactions, chat_messages")

if __name__ == "__main__":
    init()
