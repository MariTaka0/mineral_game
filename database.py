import sqlite3
import hashlib
import random
import string
import os

DB_NAME = 'school_game.db'
STUDENTS_FILE = 'students.txt'


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


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

    # Проверяем, есть ли администратор. Если база пустая — создаем учителя и студентов
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # 1. Создаем учителя
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       ("teacher", hash_password("Mineral_Admin_2026!"), "admin"))

        print("\n=== УЧИТЕЛЬ СОЗДАН ===")
        print("Логин: teacher")
        print("Пароль: Mineral_Admin_2026!")
        print("======================\n")

        # 2. Читаем список учеников из файла
        if os.path.exists(STUDENTS_FILE):
            print(f"Чтение списка учеников из {STUDENTS_FILE}...")
            with open(STUDENTS_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            print("\n=== СГЕНЕРИРОВАННЫЕ АККАУНТЫ УЧЕНИКОВ ===")
            count = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Разделяем на фамилию и имя
                parts = line.split()
                if len(parts) >= 2:
                    last_name = parts[0].lower()
                    first_name = parts[1].lower()
                    # Транслитерация для логина (если хотите, можно сделать простую замену)
                    username = f"{last_name}_{first_name}"
                else:
                    username = line.lower().replace(' ', '_')

                # Генерируем случайный пароль из 6 символов
                password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

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
    cursor.execute("SELECT mode, score, correct, total, date FROM results WHERE user_id = ? ORDER BY date DESC",
                   (user_id,))
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