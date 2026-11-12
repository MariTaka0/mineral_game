from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import json
from datetime import datetime
from functools import wraps

from database import init_db, check_user, save_result, get_user_results, get_admin_stats
from game_logic import GameLogic
from minerals_db import MINERALS_DB, get_real_image_name
from quiz_db import QUIZ_QUESTIONS
from achievements_db import ACHIEVEMENTS
from facts_db import INTERESTING_FACTS, GENERAL_FACTS
from personality_test_db import PERSONALITY_QUESTIONS, PERSONALITY_RESULTS, DEFAULT_RESULT

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mineral-game-secret-key-2026')

init_db()
logic = GameLogic()


# ===================== Декоратор авторизации =====================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ===================== Базовые маршруты =====================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('game_menu'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        user = check_user(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[1]
            return redirect(url_for('game_menu'))
        flash('Неверный логин или пароль', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ===================== Меню и игра =====================
@app.route('/menu')
@login_required
def game_menu():
    return render_template('game.html',
                           stage='menu',
                           username=session['username'])


@app.route('/start/<game_type>')
@login_required
def start_game(game_type):
    game_state = logic.start_new_game(game_type)
    if game_type == 'quiz':
        question = logic.get_quiz_question([])
        game_state['current_question'] = question
        game_state['used_questions'] = [QUIZ_QUESTIONS.index(question)]
    session['game_state'] = game_state
    return redirect(url_for('play'))


@app.route('/play')
@login_required
def play():
    game_state = session.get('game_state')
    if not game_state:
        return redirect(url_for('game_menu'))

    if game_state['stage'] == 'finished':
        return redirect(url_for('finish_game'))

    if game_state['game_type'] == 'quiz':
        question = game_state['current_question']
        return render_template('game.html',
                               stage='play_quiz',
                               game=game_state,
                               question=question,
                               question_num=game_state['questions_asked'] + 1)

    mineral = game_state['current_mineral']
    image_file = get_real_image_name(mineral['name'])
    return render_template('game.html',
                           stage='play',
                           game=game_state,
                           mineral=mineral,
                           image_file=image_file,
                           question_num=game_state['questions_asked'] + 1)


@app.route('/hint', methods=['POST'])
@login_required
def hint():
    game_state = session.get('game_state')
    if not game_state or game_state['game_type'] == 'quiz':
        return jsonify({'error': 'no hints'})

    mineral = game_state['current_mineral']
    hints_used = game_state.get('hints_used', 0)
    hint_text = logic.get_hint(mineral, hints_used)
    game_state['hints_used'] = hints_used + 1
    session['game_state'] = game_state
    return jsonify({
        'hint': hint_text,
        'hints_used': game_state['hints_used']
    })


@app.route('/guess', methods=['POST'])
@login_required
def guess():
    game_state = session.get('game_state')
    if not game_state:
        return jsonify({'error': 'no game'})

    user_answer = request.form.get('answer', '')
    game_type = game_state['game_type']

    if game_type == 'quiz':
        question = game_state['current_question']
        correct, points = logic.check_quiz_answer(user_answer, question)
        if correct:
            game_state['score'] += points
            game_state['correct_answers'] += 1
            feedback = f'✅ Верно! +{points} баллов'
        else:
            feedback = f'❌ Неверно. Правильный ответ: {question["answer"]}'

        game_state['questions_asked'] += 1

        if game_state['questions_asked'] >= game_state['max_questions']:
            game_state['stage'] = 'finished'
        else:
            question = logic.get_quiz_question(game_state['used_questions'])
            game_state['current_question'] = question
            game_state['used_questions'].append(QUIZ_QUESTIONS.index(question))

        session['game_state'] = game_state
        return jsonify({
            'correct': correct,
            'feedback': feedback,
            'score': game_state['score'],
            'finished': game_state['stage'] == 'finished',
            'redirect': url_for('finish_game') if game_state['stage'] == 'finished' else None
        })

    mineral = game_state['current_mineral']

    if game_type == 'guess_formula':
        correct, points, match_type = logic.check_formula_guess(user_answer, mineral)
    else:
        correct, points, match_type = logic.check_guess(user_answer, mineral)

    feedback = ''
    achievements = []

    if correct:
        game_state['score'] += points
        game_state['correct_answers'] += 1
        feedback = f'✅ Верно! +{points} баллов'
        if match_type == 'partial':
            feedback = f'✅ Почти! Засчитано частичное совпадение. +{points} баллов'
        achievements = logic.check_achievements(game_state, correct_type=match_type)
        fact = logic.get_fact(mineral['name'])
        feedback += f'<br><br>💡 <em>{fact}</em>'
    else:
        logic.check_achievements(game_state, correct_type=None)
        feedback = f'❌ Неверно. Правильный ответ: <strong>{mineral["name"]}</strong>'

    game_state['questions_asked'] += 1
    game_state['last_was_wrong'] = not correct

    if game_state['questions_asked'] >= game_state['max_questions']:
        game_state['stage'] = 'finished'
    else:
        new_mineral = logic.get_next_mineral(game_state['used_minerals'])
        game_state['current_mineral'] = new_mineral
        game_state['used_minerals'].append(new_mineral['name'])
        game_state['hints_used'] = 0

    session['game_state'] = game_state

    return jsonify({
        'correct': correct,
        'feedback': feedback,
        'score': game_state['score'],
        'finished': game_state['stage'] == 'finished',
        'redirect': url_for('finish_game') if game_state['stage'] == 'finished' else None,
        'achievements': [ACHIEVEMENTS[a] for a in achievements]
    })


@app.route('/finish')
@login_required
def finish_game():
    game_state = session.get('game_state')
    if not game_state:
        return redirect(url_for('game_menu'))

    save_result(
        session['user_id'],
        game_state['game_type'],
        game_state['score'],
        game_state['correct_answers'],
        game_state['questions_asked'],
        datetime.now().strftime('%Y-%m-%d %H:%M')
    )

    stats = logic.get_game_stats(game_state)
    achievements = [ACHIEVEMENTS[a] for a in game_state.get('achievements_earned', []) if a in ACHIEVEMENTS]
    session.pop('game_state', None)

    return render_template('game.html',
                           stage='finished',
                           stats=stats,
                           achievements=achievements,
                           game=game_state)


# ===================== Справочник и статистика =====================
@app.route('/reference')
@login_required
def reference():
    minerals = sorted(MINERALS_DB, key=lambda m: m['name'])
    minerals_with_images = []
    for m in minerals:
        m_copy = dict(m)
        m_copy['image_file'] = get_real_image_name(m['name'])
        minerals_with_images.append(m_copy)
    return render_template('reference.html', minerals=minerals_with_images)


@app.route('/stats')
@login_required
def stats():
    results = get_user_results(session['user_id'])
    total_games = len(results)
    total_score = sum(r[1] for r in results)
    total_correct = sum(r[2] for r in results)
    total_questions = sum(r[3] for r in results)
    accuracy = round(total_correct / total_questions * 100, 1) if total_questions else 0

    return render_template('stats.html',
                           results=results,
                           total_games=total_games,
                           total_score=total_score,
                           accuracy=accuracy)


# ===================== Админ =====================
@app.route('/admin')
@login_required
def admin():
    if session.get('role') != 'admin':
        return redirect(url_for('game_menu'))
    modes, recent = get_admin_stats()
    return render_template('admin.html', modes=modes, recent=recent)


# ===================== Тест "Кто ты из минералов?" =====================
@app.route('/personality')
@login_required
def personality_start():
    """Стартовая страница теста."""
    return render_template('personality.html', stage='start')


@app.route('/personality/test')
@login_required
def personality_test():
    """Страница с вопросами."""
    return render_template('personality.html',
                           stage='quiz',
                           questions=PERSONALITY_QUESTIONS)


@app.route('/personality/result', methods=['POST'])
@login_required
def personality_result():
    """Подсчёт результата на основе выборов."""
    answers = request.form.get('answers')

    scores = {}
    if answers:
        try:
            answers_dict = json.loads(answers)
        except (ValueError, TypeError):
            answers_dict = {}

        for q_idx, opt_idx in answers_dict.items():
            try:
                q_idx = int(q_idx)
                opt_idx = int(opt_idx)
                option = PERSONALITY_QUESTIONS[q_idx]['options'][opt_idx]
                for mineral, pts in option['scores'].items():
                    scores[mineral] = scores.get(mineral, 0) + pts
            except (IndexError, KeyError, TypeError, ValueError):
                continue

    winner = max(scores, key=scores.get) if scores else DEFAULT_RESULT
    result = PERSONALITY_RESULTS.get(winner, PERSONALITY_RESULTS[DEFAULT_RESULT])

    top3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    top3_info = [
        {
            'name': name,
            'points': pts,
            'title': PERSONALITY_RESULTS.get(name, {}).get('title', name)
        }
        for name, pts in top3
    ]

    return render_template('personality.html',
                           stage='result',
                           result=result,
                           winner=winner,
                           top3=top3_info,
                           all_scores=scores)


# ===================== API =====================
@app.route('/api/fact')
@login_required
def api_fact():
    mineral = request.args.get('mineral')
    return jsonify({'fact': logic.get_fact(mineral)})


# ===================== Точка входа =====================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
