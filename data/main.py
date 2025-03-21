from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, DeclarativeBase, sessionmaker

Base : DeclarativeBase = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, nullable=False)
    photo_path = Column(String, nullable=False)



class DataBase:
    def __init__(self, path : str):
        self.path = f"sqlite:///{path}"
        self.engine = create_engine(self.path)
        Base.metadata.create_all(self.engine)

        self.sesion = sessionmaker(bind=self.engine)

    def add_user(self, user : User):
        session = self.sesion()
        session.add(user)
        session.commit()
        session.refresh(user)  # Ensure all attributes (like id) are loaded
        session.close()
        return user

    def get_user(self, id: int) -> User:
        session = self.sesion()
        user = session.query(User).filter(User.id == id).first()
        session.close()
        return user

    def delete_user(self, id: int):
        session = self.sesion()
        user = session.query(User).filter(User.id == id).first()
        if user:
            session.delete(user)
            session.commit()
        session.close()

    def update_user(self, user: User):
        session = self.sesion()
        existing_user = session.query(User).filter(User.id == user.id).first()
        if existing_user:
            existing_user.name = user.name
            existing_user.photo_path = user.photo_path
            session.commit()
        session.close()





if __name__ == '__main__':
    db = DataBase('data.sqlite')

    user = User(id = 1, name = "sher", photo_path = "photo_path")
    # db.add_user(user)
    db.update_user(user)
    # print(user.id, user.name, user.photo_path)
    # db.delete_user(3)
    # user = db.get_user(3)
    # if user:
    #     print(user.id, user.name, user.photo_path)
    #     user.name = "Shermuhammad"
    #     db.update_user(user)