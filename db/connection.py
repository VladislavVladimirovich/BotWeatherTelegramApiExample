from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine(f'sqlite:///db/TelegramBot.db', connect_args={"check_same_thread": False})

base = declarative_base()
base.metadata.create_all(engine)

session = sessionmaker(bind=engine)()
