import sqlite3
import hashlib
import random
import string
import os

DB_NAME = 'school_game.db'
STUDENTS_FILE = 'students.txt'

# ЗАФИКСИРОВАННЫЕ ПАРОЛИ (логин: пароль)
FIXED_PASSWORDS = {
    'абмайкина_анна': 'h2yttp',
    'агафонов_андрей': 'olbffm',
    'верхошапов_максим': 'ehoc7g',
    'гайдук_дмитрий': 'nf43j0',
    'гойло_иван': '8do96m',
    'гранский_данил': 'igvole',
    'егоров_александр': '56r9mf',
    'захаров_максим': '6atu4k',
    'захаров_матвей': 'wb9n9a',
    'комаровских_данил': 'g939wg',
    'кряжева_вероника': 'pphxd3',
    'кузнецов_пётр': 'd35y73',
    'ларионов_матвей': '07q4ep',
    'лемеш_владислав': 'ycqngr',
    'луценко_дарья': '5isw1o',
    'макаров_николай': 'o2hiie',
    'малютин_андрей': '0if5gw',
    'манц_максим': 'lqbwec',
    'мельников_павел': 'dsm18d',
    'мердеева_лидия': 'txzvp8',
    'орлов_никита': 'r8zjrp',
    'пронин_георгий': '5svtt5',
    'родионов_иван': 'vdiiim',
    'савельев_сергей': 'dgk5eu',
    'сакиров_руслан': '9bczhs',
    'сараева_светлана': 'l0od1a',
    'сбродов_тимофей': 'zerk66',
    'фусс_денис': '4odv1x',
    'хамматов_ислам': 'l0qitq',
    'яблонский_денис': 'qouifr',
    'аканаева_алиса': '6cplz9',
    'андронов_евгений': 'pbcf7n',
    'арсаев_константин': 'l21iy0',
    'бардаченко_александра': 'mqnny9',
    'бурдаков_глеб': 'o3kuod',
    'камелина_анна': '6obp4q',
    'колмогорова_софья': '969j1t',
    'коротаев_антон': 'm907yo',
    'корякина_софия': 'g9owq5',
    'кручинин_илья': '4ztw6w',
    'митяев_роман': '8419od',
    'мозырев_вадим': '3ugoau',
    'новиков_захар': 'aq5n1y',
    'овчинников_виктор': 'th2zsn',
    'орлова_ангелина': 'xle8f3',
    'палий_полина': 'jriohj',
    'погребняк_мария': 'x9v3dc',
    'поздеева_софья': 'r8gc66',
    'политова_юлия': 'c9vhrq',
    'потапова_кира': 'dyn9yd',
    'садыгова_лейла': 'hbmot7',
    'сингаевский_роман': 'iauprl',
    'сязи_дмитрий': 'xnl01b',
    'трошина_анастасия': 's30ccc',
    'ульянов_константин': 'fbsldz',
    'фаттахов_никита': '1xkryb',
    'хундякова_алина': '3rh4yf',
    'чепелев_алексей': 'ehrano',
    'юдашкин_александр': 'gtgt6y',
    'янц_мария': 'yl6mbo',
    'арсеньева_анна': 's42y05',
    'бикташев_артур': 'o3iwmu',
    'боровкова_анна': '23n5p9',
    'гончарова_полина': 'gjevse',
    'даутова_диана': 'ml8ky0',
    'дещеня_марк': 'nzpohq',
    'зелева_эвелина': '6cvxro',
    'иванчишин_надежда': '8ovfit',
    'иванюхина_дарья': 'pmy2op',
    'кожина_анна': '5f8ie3',
    'коротков_александр': 'zzlifv',
    'корякина_анастасия': 'g3oqms',
    'коряков_даниил': 'twvv8c',
    'костюкова_ирина': '22zpg9',
    'летушов_евгений': 'yrivn5',
    'масленников_владислав': 'ibzpzk',
    'николаев_глеб': 'sg4hkq',
    'оборин_даниил': 'b51dvn',
    'овчинников_дмитрий': 'o8uv9g',
    'парамонов_прохор': '3zg76w',
    'петрова_ксения': 'm9acq2',
    'почтарёва_валерия': 'l3csqy',
    'рехачев_тимофей': 'dze23k',
    'соловьева_екатерина': 'rx40dp',
    'степанов_илья': 'k0d74f',
    'усакина_виктория': 'blg6j2',
    'фомин_кирилл': '6qy9uu',
    'фрикцел_максим': 'zjjdh0',
    'чунихина_арина': '4j8ope',
    'энгельман_наталья': 'too4f3',
    'арсибекова_александра': 'yil15a',
    'белова_лилия': '36v00j',
    'бранзбург_алексей': 'm2r5go',
    'волков_арсений': 'tpn8b4',
    'григорьев_георгий': 'xoz5iy',
    'гук_влада': '2v3nnh',
    'евграфов_даниил': 'fuiwwu',
    'ермаков_павел': 'czrh7h',
    'завада_ольга': 'on48rq',
    'истигнеева_арина': 'sv97x1',
    'кадочкин_иван': 'zk39sl',
    'касиев_тимур': 'yrsns9',
    'кириченко_валерия': 'kali9h',
    'кравец_сергей': '89mmh8',
    'куценко_никита': 'lqvb1b',
    'лисеенко_анастасия': 'dbuxt8',
    'михайлов_александр': 'aylno6',
    'москвина_анастасия': 'jogsxo',
    'мухин_никита': '9ot5kz',
    'налобин_павел': 'dfrtyi',
    'поступинский_александр': 'it31sa',
    'рамазанова_кунсулу': 'n9j1q3',
    'рахимова_элина': 'f3d3h4',
    'риффель_арина': 'nj3c98',
    'сальникова_карина': 'x7mx3c',
    'солотина_валерий': 'q6cogp',
    'третьяк_денис': 'ltqdim',
    'хакова_арина': '5w8msp',
    'храмов_евсей': 'k82fxj',
    'хусаинова_валерия': 'ofie15',
}

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
    
    # Проверяем, есть ли пользователи в базе
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Создаем учителя
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       ("teacher", hash_password("Mineral_Admin_2026!"), "admin"))
        
        print("\n=== УЧИТЕЛЬ СОЗДАН ===")
        print("Логин: teacher")
        print("Пароль: Mineral_Admin_2026!")
        print("======================\n")

        # Читаем список учеников
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
                    
                parts = line.split()
                if len(parts) >= 2:
                    last_name = parts[0].lower()
                    first_name = parts[1].lower()
                    username = f"{last_name}_{first_name}"
                else:
                    username = line.lower().replace(' ', '_')
                
                # Берем пароль из зафиксированного словаря, если есть
                password = FIXED_PASSWORDS.get(username)
                if not password:
                    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                    print(f"⚠️ Для {username} нет зафиксированного пароля. Сгенерирован новый: {password}")
                
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
