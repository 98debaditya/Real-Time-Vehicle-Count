import mysql.connector as msq
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

host = 'localhost'
user = 'username'
password = 'password'
table_name = user

connection = msq.connect(
    host=host,
    user=user,
    password=password,
    database=user
)

cursor = connection.cursor()
create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        date DATE,
        count INT
    )
"""
cursor.execute(create_table_query)
