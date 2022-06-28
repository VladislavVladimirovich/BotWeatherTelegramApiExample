from sqlalchemy import Column, Integer, String
from .connection import base


class Users(base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    userName = Column(String, nullable=True)
    lastName = Column(String, nullable=True)
    firstName = Column(String, nullable=True)
    updateId = Column(Integer, nullable=True, default=0)

    def __repr__(self):
        return f'<id={self.id}, lastName={self.lastName}, firstName={self.firstName}, updateId={self.updateId}>'


class ImageWeather(base):
    __tablename__ = 'image_weather'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    path = Column(String, nullable=True)
    telegram_key = Column(String, nullable=True)

    def __repr__(self):
        return f'<id={self.id}, name={self.name}, path={self.path}, telegram_key={self.telegram_key}>'