# import pandas as pd 
# import os
# from datetime import datetime, timedelta
# from data import User




# uzbek_months = {
#     1: "yanvar",
#     2: "fevral",
#     3: "mart",
#     4: "aprel",
#     5: "may",
#     6: "iyun",
#     7: "iyul",
#     8: "avgust",
#     9: "sentabr",
#     10: "oktabr",
#     11: "noyabr",
#     12: "dekabr"
# }

# def load_csv(file_path : str)-> pd.DataFrame:
#     if os.path.exists(file_path):
#         df = pd.read_csv(file_path)
#     else:
#         df = pd.DataFrame(columns=["id", "isim"])
#         df.to_csv(file_path, index=False)
#     return df



# class Group:
#     def __init__(self, name : str, create : bool = False):
#         if create and not os.path.exists(f"marks/{name}"):
#             os.makedirs(f"marks/{name}")
#         self.name = name
#         self.df = pd.read_csv(self.file_path)
    

#     def update_df(self) -> pd.DataFrame:
#         self.df = pd.read_csv(self.file_path)

#     @property
#     def file_path(self) -> str:
#         now = datetime.now()
#         path = f"marks/{self.name}/{uzbek_months.get(now.month)}_{now.year}.csv"
#         if not os.path.exists(path):
#             df = pd.DataFrame(columns=["id", "isim"])
#             df.to_csv(path, index=False)
            
#         return path
    
    
#     @property
#     def today_column(self) -> str:
#         now = datetime.now()
#         return now.strftime("%d.%m.%Y")
    
#     def is_marked(self, user: User) -> bool:
#         self.update_df()
#         if self.today_column not in self.df.columns:
#             self.df[self.today_column] = "-"
#             self.df.to_csv(self.file_path, index=False)

#         user_data = self.df.loc[self.df['id'] == user.id]
#         if not user_data.empty:
#             mark = user_data[self.today_column].iloc[0]
#             if mark == '-':
#                 self.df.loc[self.df['id'] == user.id, self.today_column] = '+'
#                 self.df.to_csv(self.file_path, index=False)
#                 return False
#         else:
#             new_user = {"id": user.id, "isim": user.name}
#             for col in self.df.columns:
#                 if col not in ["id", "isim"]:
#                     new_user[col] = "-"
#             new_user[self.today_column] = "+"
#             self.df = pd.concat([self.df, pd.DataFrame([new_user])], ignore_index=True)
#             self.df = self.df.sort_values(by="isim").reset_index(drop=True)
#             self.df.to_csv(self.file_path, index=False)
#             return False
#         return True


# df = Group('3-guruh', create=True)
# user = User()
# user.name = "Obid asamov"
# user.id = 3
# user.group = 'test guruh'
# print(df.is_marked(user))


# # print(df.columns)
# # print()

from data import DataBase, User, Group
import asyncio



db = DataBase('data/data.sqlite')
u = User()
u.name = "sher"
u.group = 'test'
u.photo_path = 'blah'

user = db.add_user(u)
if user:
    print(user.name, user.id, user.group)