import sqlite3
from datetime import datetime
import os

# Use data directory for database (Docker-friendly)
DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_NAME = os.path.join(DATA_DIR, "bot.db")

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            word TEXT NOT NULL,
            definition TEXT,
            repetition_level INTEGER DEFAULT 0,
            next_review_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT OR IGNORE INTO users (id) VALUES (?)', (user_id,))
        conn.commit()
    finally:
        conn.close()

def add_word(user_id, word, definition, next_review_at):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO words (user_id, word, definition, repetition_level, next_review_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, word, definition, 0, next_review_at))
        conn.commit()
    finally:
        conn.close()

def get_due_words(user_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        now = datetime.now()
        c.execute('''
            SELECT * FROM words 
            WHERE user_id = ? AND next_review_at <= ?
            ORDER BY next_review_at ASC
        ''', (user_id, now))
        return c.fetchall()
    finally:
        conn.close()

def get_word(word_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM words WHERE id = ?', (word_id,))
        return c.fetchone()
    finally:
        conn.close()

def update_word_progress(word_id, new_level, next_review_at):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE words 
            SET repetition_level = ?, next_review_at = ?
            WHERE id = ?
        ''', (new_level, next_review_at, word_id))
        conn.commit()
    finally:
        conn.close()

def get_all_user_words(user_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            SELECT * FROM words 
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        return c.fetchall()
    finally:
        conn.close()

