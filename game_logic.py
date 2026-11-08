import random
from minerals_db import MINERALS_DB
from quiz_db import QUIZ_QUESTIONS
from facts_db import INTERESTING_FACTS, GENERAL_FACTS
from achievements_db import ACHIEVEMENTS


class GameLogic:
    def __init__(self):
        pass

    def start_new_game(self, game_type='guess_photo'):
        if game_type == 'guess_photo':
            mineral = random.choice(MINERALS_DB)
            return {
                'game_type': 'guess_photo',
                'current_mineral': mineral,
                'score': 0,
                'questions_asked': 0,
                'max_questions': 5,
                'hints_used': 0,
                'stage': 'playing',
                'used_minerals': [mineral['name']],
                'last_was_wrong': False,
                'consecutive_correct': 0,
                'achievements_earned': [],
                'modes_played': ['guess_photo']
            }
        elif game_type == 'guess_description':
            mineral = random.choice(MINERALS_DB)
            return {
                'game_type': 'guess_description',
                'current_mineral': mineral,
                'score': 0,
                'questions_asked': 0,
                'max_questions': 5,
                'hints_used': 0,
                'stage': 'playing',
                'used_minerals': [mineral['name']],
                'last_was_wrong': False,
                'consecutive_correct': 0,
                'achievements_earned': [],
                'modes_played': ['guess_description']
            }
        elif game_type == 'guess_formula':
            mineral = random.choice(MINERALS_DB)
            return {
                'game_type': 'guess_formula',
                'current_mineral': mineral,
                'score': 0,
                'questions_asked': 0,
                'max_questions': 5,
                'hints_used': 0,
                'stage': 'playing',
                'used_minerals': [mineral['name']],
                'last_was_wrong': False,
                'consecutive_correct': 0,
                'achievements_earned': [],
                'modes_played': ['guess_formula']
            }
        elif game_type == 'quiz':
            return {
                'game_type': 'quiz',
                'score': 0,
                'questions_asked': 0,
                'max_questions': 5,
                'stage': 'playing',
                'current_question': None,
                'used_questions': [],
                'consecutive_correct': 0,
                'achievements_earned': [],
                'modes_played': ['quiz']
            }

    def check_guess(self, user_answer, current_mineral):
        user_answer_lower = user_answer.lower().strip()
        name_lower = current_mineral['name'].lower()

        if user_answer_lower == name_lower:
            return True, 10, 'perfect'

        name_clean = name_lower.replace('кпш-', '').replace('*', '').strip()
        answer_clean = user_answer_lower.replace('*', '').strip()

        if answer_clean == name_clean:
            return True, 10, 'perfect'

        if name_clean in answer_clean or answer_clean in name_clean:
            return True, 8, 'partial'

        if user_answer_lower == current_mineral['formula'].lower():
            return True, 5, 'formula'

        return False, 0, None

    def check_formula_guess(self, user_answer, current_mineral):
        user_answer_lower = user_answer.lower().strip()
        name_lower = current_mineral['name'].lower()

        if user_answer_lower == name_lower:
            return True, 10, 'perfect'

        name_clean = name_lower.replace('кпш-', '').replace('*', '').strip()
        answer_clean = user_answer_lower.replace('*', '').strip()

        if answer_clean == name_clean:
            return True, 10, 'perfect'

        if name_clean in answer_clean or answer_clean in name_clean:
            return True, 8, 'partial'

        return False, 0, None

    def get_hint(self, current_mineral, hints_used):
        if hints_used < len(current_mineral['hints']):
            return current_mineral['hints'][hints_used]
        return "Подсказок больше нет! Попробуй угадать самостоятельно."

    def get_next_mineral(self, used_minerals):
        available = [m for m in MINERALS_DB if m['name'] not in used_minerals]
        if not available:
            available = MINERALS_DB
        return random.choice(available)

    def get_quiz_question(self, used_questions):
        available = [q for i, q in enumerate(QUIZ_QUESTIONS) if i not in used_questions]
        if not available:
            available = QUIZ_QUESTIONS
        return random.choice(available)

    def check_quiz_answer(self, user_answer, question):
        user_answer_lower = user_answer.lower().strip()
        correct_answer = question['answer'].lower().strip()

        if user_answer_lower == correct_answer:
            return True, 5

        if correct_answer in user_answer_lower or user_answer_lower in correct_answer:
            return True, 3

        return False, 0

    def get_game_stats(self, game_state):
        max_possible = game_state['max_questions'] * 10
        return {
            'score': game_state['score'],
            'questions_asked': game_state['questions_asked'],
            'max_questions': game_state['max_questions'],
            'remaining': game_state['max_questions'] - game_state['questions_asked'],
            'accuracy': round((game_state['score'] / max_possible) * 100, 1) if game_state['questions_asked'] > 0 else 0,
            'achievements': game_state.get('achievements_earned', [])
        }

    def check_achievements(self, game_state, correct_type=None, was_hint=False):
        earned = []

        if correct_type == 'perfect' and game_state.get('hints_used', 0) == 0:
            if 'perfect_round' not in game_state.get('achievements_earned', []):
                earned.append('perfect_round')
                game_state['score'] += ACHIEVEMENTS['perfect_round']['points_bonus']

        if correct_type and game_state.get('hints_used', 0) >= 2:
            if 'hint_master' not in game_state.get('achievements_earned', []):
                earned.append('hint_master')
                game_state['score'] += ACHIEVEMENTS['hint_master']['points_bonus']

        if correct_type and game_state.get('last_was_wrong', False):
            if 'comeback' not in game_state.get('achievements_earned', []):
                earned.append('comeback')
                game_state['score'] += ACHIEVEMENTS['comeback']['points_bonus']

        game_state['last_was_wrong'] = not bool(correct_type)

        if correct_type:
            game_state['consecutive_correct'] = game_state.get('consecutive_correct', 0) + 1
            if game_state['consecutive_correct'] >= 3:
                if 'geology_expert' not in game_state.get('achievements_earned', []):
                    earned.append('geology_expert')
                    game_state['score'] += ACHIEVEMENTS['geology_expert']['points_bonus']
        else:
            game_state['consecutive_correct'] = 0

        if 'achievements_earned' not in game_state:
            game_state['achievements_earned'] = []
        game_state['achievements_earned'].extend(earned)

        return earned

    def get_fact(self, mineral_name=None):
        if mineral_name and mineral_name in INTERESTING_FACTS:
            return random.choice(INTERESTING_FACTS[mineral_name])
        return random.choice(GENERAL_FACTS)

    def get_achievement_info(self, key):
        return ACHIEVEMENTS.get(key, {})
