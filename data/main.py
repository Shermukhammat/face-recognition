from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, DeclarativeBase, sessionmaker
import pandas as pd 
import os, sys
from datetime import datetime, timedelta
import json

def resource_path(relative_path):
    """ Get absolute path to resource, works for development and PyInstaller EXE """
    if getattr(sys, 'frozen', False):  # If running as compiled EXE
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

Base : DeclarativeBase = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, nullable=False)
    group = Column(String)
    photo_path = Column(String, nullable=False)

uzbek_months = {
    1: "yanvar",
    2: "fevral",
    3: "mart",
    4: "aprel",
    5: "may",
    6: "iyun",
    7: "iyul",
    8: "avgust",
    9: "sentabr",
    10: "oktabr",
    11: "noyabr",
    12: "dekabr"
}

def load_csv(file_path : str)-> pd.DataFrame:
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=["id", "isim"])
        df.to_csv(file_path, index=False)
    return df



class Group:
    def __init__(self, name : str, create : bool = False):
        if create and not os.path.exists(resource_path(f"marks/{name}")):
            os.makedirs(resource_path(f"marks/{name}"))
        self.name = name
        self.df = pd.read_csv(self.file_path)
    

    def update_df(self) -> pd.DataFrame:
        self.df = pd.read_csv(self.file_path)

    @property
    def file_path(self) -> str:
        now = datetime.now()
        path = resource_path(f"marks/{self.name}/{uzbek_months.get(now.month)}_{now.year}.csv")
        if not os.path.exists(path):
            df = pd.DataFrame(columns=["id", "isim"])
            df.to_csv(path, index=False)
            
        return path
    
    @property
    def excels_path(self) -> list[str]:
        path = resource_path(f"marks/{self.name}")
        data = []
        if os.path.exists(path):
            for file_name in os.listdir(path):
                if file_name.endswith(".csv"):
                    df = pd.read_csv(resource_path(f"marks/{self.name}/{file_name}"))
                    df.to_excel(resource_path(f"marks/{self.name}/{file_name.replace('.csv', '.xlsx')}"), index=False)

            for file_name in os.listdir(path):
                if file_name.endswith(".xlsx"):
                    data.append(resource_path(f"marks/{self.name}/{file_name}"))
        return data


    @property
    def today_column(self) -> str:
        now = datetime.now()
        return now.strftime("%d.%m.%Y")
    
    def is_marked(self, user: User) -> bool:
        self.update_df()
        if self.today_column not in self.df.columns:
            self.df[self.today_column] = "-"
            self.df.to_csv(self.file_path, index=False)

        user_data = self.df.loc[self.df['id'] == user.id]
        if not user_data.empty:
            mark = user_data[self.today_column].iloc[0]
            if mark == '-':
                self.df.loc[self.df['id'] == user.id, self.today_column] = '+'
                self.df.to_csv(self.file_path, index=False)
                return False
        else:
            new_user = {"id": user.id, "isim": user.name}
            for col in self.df.columns:
                if col not in ["id", "isim"]:
                    new_user[col] = "-"
            new_user[self.today_column] = "+"
            self.df = pd.concat([self.df, pd.DataFrame([new_user])], ignore_index=True)
            self.df = self.df.sort_values(by="isim").reset_index(drop=True)
            self.df.to_csv(self.file_path, index=False)
            return False
        return True



class Groups(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, nullable=False)

class LastIds(Base):
    __tablename__ = "last_id"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)

class DataBase:
    def __init__(self, path : str, json_path: str = 'last.json'):
        self.path = f"sqlite:///{path}"
        self.json_path = json_path
        self.engine = create_engine(self.path)
        Base.metadata.create_all(self.engine)

        self.sesion = sessionmaker(bind=self.engine)

    @property
    def new_id(self) -> int:
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r') as file:
                last_ids = json.load(file)
        else:
            last_ids = {}

        last_id = last_ids.get("last_id", 1)
        last_id += 1
        last_ids["last_id"] = last_id

        with open(self.json_path, 'w') as file:
            json.dump(last_ids, file)

        return last_id
    
    def add_user(self, user: User):
        session = self.sesion()
        # Check if the user ID is provided
        if not user.id:
            user.id = self.new_id

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

    def delet_group_users(self, group_name: str):
        session = self.sesion()
        users = session.query(User).filter(User.group == group_name).all()
        if users:
            for user in users:
                session.delete(user)
            session.commit()
        session.close()

    def get_group_users(self, group_name: str) -> list[User]:
        session = self.sesion()
        users = session.query(User).filter(User.group == group_name).all()
        session.close()
        return users

    def update_user(self, user: User):
        session = self.sesion()
        existing_user = session.query(User).filter(User.id == user.id).first()
        if existing_user:
            existing_user.name = user.name
            existing_user.photo_path = user.photo_path
            session.commit()
        session.close()

    
    @property
    def groups(self) -> list[Group]:
        session = self.sesion()
        groups = session.query(Groups.name).all()
        session.close()
        return [Group(group.name) for group in groups]

    def get_group(self, name : str) -> Group:
        session = self.sesion()
        group = session.query(Groups.name).filter(Groups.name == name).first()
        session.close()
        if group:
            return Group(group.name)
    
    def delete_group(self, name: str) -> bool:
        session = self.sesion()
        group = session.query(Groups).filter(Groups.name == name).first()
        if group:
            session.delete(group)
            session.commit()
            session.close()
            return True
        session.close()
        return False

    def add_group(self, name: str) -> bool:
        session = self.sesion()
        existing_group = session.query(Groups).filter(Groups.name == name).first()
        if existing_group:
            session.close()
            return False
        new_group = Groups(name=name)
        session.add(new_group)
        session.commit()
        session.close()
        return True

    def get_last_users(self, limit: int = 50) -> list[User]:
        session = self.sesion()
        users = session.query(User).order_by(User.id.desc()).limit(limit).all()
        session.close()
        return users

    def search_users(self, name: str) -> list[User]:
        session = self.sesion()
        users = session.query(User).filter(User.name.ilike(f"%{name.lower()}%")).all()
        session.close()
        return users



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