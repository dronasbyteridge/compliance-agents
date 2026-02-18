import mysql.connector
from contextlib import contextmanager
from app.config import MYSQL_CONFIG

@contextmanager
def get_db():
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = connection.cursor(dictionary=True)
    try:
        yield connection, cursor
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()
