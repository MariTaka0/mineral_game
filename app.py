from flask import Flask, render_template, request, redirect, url_for, session, flash
import datetime
from database import init_db, check_user, save_result, get_user_results, get_admin_stats
from game_logic import GameLogic
from minerals_db import MINERALS_DB, get_real_image_name
from quiz_db import QUIZ_QUESTIONS

app = Flask(__name__)
app.secret_key = 'super_secret_mineral_key_2026'

game_logic = GameLogic()


@app.before_request
def setup():
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('game_menu'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_user(username, password)

        if user:
            session['user_id'] = user[0]
            session['role'] = user[1]
            session['username'] = username
            return redirect(url_for('game_menu'))
        else:
            flash('Неверный логин или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/menu')
def game_menu():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('game.html', username=session['username'])


@app.route('/reference')
def reference():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    minerals_with_images = []
    for mineral in MINERALS_DB:
        mineral_copy = mineral.copy()
        mineral_copy['real_image'] = get_real_image_name(mineral['name'])
        minerals_with_images.append(mineral_copy)

    return render_template('reference.html', minerals=minerals_with_images, username=session['username'])


@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_results = get_user_results(session['user_id'])
    return render_template('stats.html', results=user_results)


@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return "Доступ запрещен", 403
    modes, recent_games = get_admin_stats()
    return render_template('admin.html', modes=modes, recent_games=recent_games)


@app.route('/api/start_game', methods=['POST'])
def api_start_game():
    if 'user_id' not in session:
        return {"error": "Unauthorized"}, 401

    mode = request.json.get('mode')
    game_state = game_logic.start_new_game(mode)
    session['game_state'] = game_state

    if mode == 'quiz':
        question = game_logic.get_quiz_question([])
        game_state['current_question'] = question
        for i, q in enumerate(QUIZ_QUESTIONS):
            if q['question'] == question['question']:
                game_state['used_questions'] = [i]
                break
        session['game_state'] = game_state
        return {
            "game_type": "quiz",
            "questions_asked": 0,
            "max_questions": game_state['max_questions'],
            "current_mineral": question
        }

    if mode == 'guess_photo':
        game_state['current_mineral']['real_image'] = get_real_image_name(game_state['current_mineral']['name'])
        session['game_state'] = game_state

    return game_state


@app.route('/api/check_answer', methods=['POST'])
def api_check_answer():
    if 'user_id' not in session or 'game_state' not in session:
        return {"error": "No active game"}, 400

    game_state = session['game_state']
    user_answer = request.json.get('answer').strip()
    game_type = game_state['game_type']

    is_correct = False
    points = 0
    correct_text = ""
    fact = ""

    if game_type in ['guess_photo', 'guess_description', 'guess_formula']:
        current = game_state['current_mineral']
        if game_type == 'guess_formula':
            is_correct, points, correct_type = game_logic.check_formula_guess(user_answer, current)
        else:
            is_correct, points, correct_type = game_logic.check_guess(user_answer, current)

        correct_text = current['name']
        fact = game_logic.get_fact(current['name'])

        if is_correct:
            game_state['score'] += points
            game_state['correct_answers'] = game_state.get('correct_answers', 0) + 1
        game_logic.check_achievements(game_state, correct_type)

    elif game_type == 'quiz':
        question = game_state['current_question']
        is_correct, points = game_logic.check_quiz_answer(user_answer, question)

        correct_text = question['answer']
        fact = game_logic.get_fact()

        if is_correct:
            game_state['score'] += points
            game_state['correct_answers'] = game_state.get('correct_answers', 0) + 1
        game_logic.check_achievements(game_state, 'perfect' if is_correct else None)

    game_state['questions_asked'] += 1
    is_end = game_state['questions_asked'] >= game_state['max_questions']

    if not is_end:
        if game_type == 'quiz':
            next_q = game_logic.get_quiz_question(game_state['used_questions'])
            game_state['current_question'] = next_q
            for i, q in enumerate(QUIZ_QUESTIONS):
                if q['question'] == next_q['question']:
                    game_state['used_questions'].append(i)
                    break
        else:
            next_mineral = game_logic.get_next_mineral(game_state['used_minerals'])
            game_state['current_mineral'] = next_mineral
            game_state['used_minerals'].append(next_mineral['name'])
            game_state['hints_used'] = 0
    else:
        mode_names = {
            'guess_photo': 'По фото',
            'guess_description': 'По описанию',
            'guess_formula': 'По формуле',
            'quiz': 'Викторина'
        }
        save_result(
            session['user_id'], mode_names.get(game_type, game_type),
            game_state['score'], game_state.get('correct_answers', 0),
            game_state['max_questions'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        )

    session['game_state'] = game_state

    return {
        "correct": is_correct,
        "points": points,
        "correct_answer": correct_text,
        "fact": fact,
        "is_end": is_end,
        "score": game_state['score']
    }


@app.route('/api/next_round', methods=['POST'])
def api_next_round():
    if 'user_id' not in session or 'game_state' not in session:
        return {"error": "No active game"}, 400

    game_state = session['game_state']
    game_type = game_state['game_type']

    if game_type == 'quiz':
        current_item = game_state['current_question']
        display_item = {"question": current_item['question']}
    else:
        display_item = game_state['current_mineral']
        if game_type == 'guess_photo':
            display_item['real_image'] = get_real_image_name(display_item['name'])
            game_state['current_mineral'] = display_item
            session['game_state'] = game_state

    return {
        "game_type": game_type,
        "questions_asked": game_state['questions_asked'],
        "max_questions": game_state['max_questions'],
        "current_mineral": display_item
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
