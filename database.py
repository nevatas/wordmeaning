import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

# Get DATABASE_URL from environment (Railway provides this automatically)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Create a connection to PostgreSQL database"""
    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL не установлена! "
            "Добавьте переменную окружения DATABASE_URL в Railway.\n"
            "Инструкция: https://github.com/nevatas/wordmeaning/blob/main/RAILWAY_SETUP.md"
        )
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                word TEXT NOT NULL,
                definition TEXT,
                repetition_level INTEGER DEFAULT 0,
                next_review_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
    finally:
        c.close()
        conn.close()

def add_user(user_id):
    """Add a new user or ignore if exists"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (id) VALUES (%s) ON CONFLICT (id) DO NOTHING', (user_id,))
        conn.commit()
    finally:
        c.close()
        conn.close()

def add_word(user_id, word, definition, next_review_at):
    """Add a new word to user's vocabulary"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO words (user_id, word, definition, repetition_level, next_review_at)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, word, definition, 0, next_review_at))
        conn.commit()
    finally:
        c.close()
        conn.close()

def get_due_words(user_id):
    """Get all words that are due for review"""
    conn = get_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    try:
        now = datetime.now()
        c.execute('''
            SELECT * FROM words 
            WHERE user_id = %s AND next_review_at <= %s
            ORDER BY next_review_at ASC
        ''', (user_id, now))
        return c.fetchall()
    finally:
        c.close()
        conn.close()

def get_word(word_id):
    """Get a specific word by ID"""
    conn = get_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    try:
        c.execute('SELECT * FROM words WHERE id = %s', (word_id,))
        return c.fetchone()
    finally:
        c.close()
        conn.close()

def update_word_progress(word_id, new_level, next_review_at):
    """Update word's repetition progress"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE words 
            SET repetition_level = %s, next_review_at = %s
            WHERE id = %s
        ''', (new_level, next_review_at, word_id))
        conn.commit()
    finally:
        c.close()
        conn.close()

def get_all_user_words(user_id):
    """Get all words for a user"""
    conn = get_connection()
    c = conn.cursor(cursor_factory=RealDictCursor)
    try:
        c.execute('''
            SELECT * FROM words 
            WHERE user_id = %s
            ORDER BY created_at DESC
        ''', (user_id,))
        return c.fetchall()
    finally:
        c.close()
        conn.close()

def delete_word_by_id(word_id):
    """Delete a word by its ID"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM words WHERE id = %s', (word_id,))
        conn.commit()
        return c.rowcount > 0
    finally:
        c.close()
        conn.close()

def delete_word_by_text(user_id, word_text):
    """Delete a word by its text content"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('DELETE FROM words WHERE user_id = %s AND word = %s', (user_id, word_text))
        conn.commit()
        return c.rowcount > 0
    finally:
        c.close()
        conn.close()
