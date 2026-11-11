import sqlite3
import hashlib
import random
import string
import os

DB_NAME = 'school_game.db'
STUDENTS_FILE = 'students.txt'
PASSWORDS_FILE = 'passwords.txt'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_saved_passwords():
    """Читает сохраненные пароли из файла."""
    passwords = {}
    if os.path.exists(PASSWORDS_FILE):
        with open(PASSWORDS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 2:
                    username = parts[0].strip()
                    password = parts[1].strip()
                    passwords[username] = password
    return passwords

def save_password(username, password, full_name):
    """Сохраняет логин и пароль в файл."""
    with open(PASSWORDS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{username} | {password} | {full_name}\n")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    ''')
    
    # Таблица результатов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mode TEXT,
            score INTEGER,
            correct INTEGER,
            total INTEGER,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Проверяем, есть ли пользователи в базе
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Создаем учителя (если его еще нет)
        teacher_password = "Mineral_Admin_2026!"
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       ("teacher", hash_password(teacher_password), "admin"))
        
        print("\n=== УЧИТЕЛЬ СОЗДАН ===")
        print(f"Логин: teacher")
        print(f"Пароль: {teacher_password}")
        print("======================\n")

        # Читаем список учеников
        if os.path.exists(STUDENTS_FILE):
            print(f"Чтение списка учеников из {STUDENTS_FILE}...")
            with open(STUDENTS_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Загружаем ранее сохраненные пароли (если есть)
            saved_passwords = load_saved_passwords()
            if saved_passwords:
                print(f"Найдены сохраненные пароли в {PASSWORDS_FILE}. Используем их.")
            
            print("\n=== СГЕНЕРИРОВАННЫЕ АККАУНТЫ УЧЕНИКОВ ===")
            count = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 2:
                    last_name = parts[0].lower()
                    first_name = parts[1].lower()
                    username = f"{last_name}_{first_name}"
                else:
                    username = line.lower().replace(' ', '_')
                
                # Если пароль уже сохранен — используем его. Иначе генерируем новый.
                if username in saved_passwords:
                    password = saved_passwords[username]
                else:
                    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                    # Сохраняем новый пароль в файл
                    save_password(username, password, line)
                
                try:
                    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                                   (username, hash_password(password)))
                    print(f"Логин: {username:25} | Пароль: {password}  ({line})")
                    count += 1
                except sqlite3.IntegrityError:
                    print(f"⚠️ Ученик {line} уже есть в базе (пропущен)")
            
            print(f"========================================\nВсего создано учеников: {count}\n")
        else:
            print(f"⚠️ Файл {STUDENTS_FILE} не найден! Созданы только учитель.")
            print("Создайте файл students.txt с именами учеников и перезапустите.")
    
    conn.commit()
    conn.close()

def check_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users WHERE username = ? AND password_hash = ?", 
                   (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user

def save_result(user_id, mode, score, correct, total, date_str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO results (user_id, mode, score, correct, total, date) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, mode, score, correct, total, date_str)
    )
    conn.commit()
    conn.close()

def get_user_results(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT mode, score, correct, total, date FROM results WHERE user_id = ? ORDER BY date DESC", (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_admin_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT mode, COUNT(*), AVG(score) FROM results GROUP BY mode")
    modes = cursor.fetchall()
    cursor.execute('''SELECT u.username, r.mode, r.score, r.correct, r.total, r.date 
                      FROM results r JOIN users u ON r.user_id = u.id ORDER BY r.date DESC LIMIT 50''')
    recent_games = cursor.fetchall()
    conn.close()
    return modes, recent_games
