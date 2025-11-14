import sqlite3
import os

DB_NAME = "todo.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task TEXT,
            done INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_task(user_id, task):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)", (user_id, task))
    conn.commit()
    conn.close()

def get_tasks(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, task, done FROM tasks WHERE user_id = ? ORDER BY id", (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def complete_task(task_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?", (task_id, user_id))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0
