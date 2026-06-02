import sqlite3
import pandas as pd

def get_db_connection():
    conn = sqlite3.connect('zzoks.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            card_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            dob TEXT,
            jmbg TEXT,
            insurer_number TEXT,
            gender TEXT,
            deactivation_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_family_by_insurer(insurer_number):
    conn = get_db_connection()
    query = "SELECT * FROM cards WHERE insurer_number = ?"
    df = pd.read_sql_query(query, conn, params=(insurer_number,))
    conn.close()
    return df

# THIS FUNCTION MUST BE HERE, AT THE BOTTOM, WITHOUT INDENTATION
def insert_card(data_dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO cards (card_id, first_name, last_name, dob, jmbg, insurer_number, gender, deactivation_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data_dict['card_id'], data_dict['first_name'], data_dict['last_name'],
            data_dict['dob'], data_dict['jmbg'], data_dict['insurer_number'],
            data_dict['gender'], data_dict['deactivation_date']
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()