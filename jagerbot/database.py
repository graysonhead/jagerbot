# from sqlalchemy import String, Column, Integer, ForeignKey, Float, DateTime, Table, func
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# import os
# from sqlalchemy.orm import sessionmaker, backref, relationship
# import config
# from discord import ActivityType
# import time
#
# basedir = os.path.abspath(os.path.dirname(__file__))
# db_constring = 'sqlite:///' + os.path.join(basedir, 'app.db?check_same_thread=False')
# print(db_constring)
# engine = create_engine(db_constring)
# Session = sessionmaker()
# Session.configure(bind=engine)
#
# Base = declarative_base()