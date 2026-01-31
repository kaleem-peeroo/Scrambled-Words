from flask import Flask, render_template, session, redirect, url_for
from wordfreq import zipf_frequency
import random
import nltk
import logging
from rich import print
from rich.panel import Panel

app = Flask(__name__)
app.secret_key = 'super secret key'

# Disable werkzeug logger
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Download brown corpus if not already downloaded
try:
    nltk.data.find('corpora/brown')
except nltk.downloader.DownloadError:
    nltk.download('brown')

ALL_NOUNS = [
    w.lower()
    for w, t in nltk.corpus.brown.tagged_words(tagset="universal")
    if t == "NOUN" and w.isalpha() and 3 <= len(w) <= 12
]


def get_words(count=5, difficulty="easy"):
    common_words = [w for w in ALL_NOUNS if zipf_frequency(w, "en") >= 4]
    if difficulty == "easy":
        pool = [w for w in common_words if 3 <= len(w) <= 5]

    elif difficulty == "medium":
        pool = [w for w in common_words if 6 <= len(w) <= 8]

    elif difficulty == "hard":
        pool = [w for w in common_words if 9 <= len(w) <= 12]

    else:
        pool = sorted(common_words, key=lambda w: len(w))

    return random.sample(pool, count)


def get_game_words():
    session['easy_words'] = get_words(20, "easy")
    session['medium_words'] = get_words(20, "medium")
    session['hard_words'] = get_words(10, "hard")
    session['difficulty'] = 'easy'
    session['word_index'] = 0


@app.route('/')
def home():
    if 'difficulty' not in session:
        get_game_words()
        session['is_scrambled'] = True

    difficulty = session['difficulty']
    word_index = session.get('word_index', 0)
    is_scrambled = session.get('is_scrambled', True)

    if difficulty == 'easy' and word_index >= len(session['easy_words']):
        session['difficulty'] = 'medium'
        session['word_index'] = 0
        difficulty = 'medium'
        word_index = 0
    elif difficulty == 'medium' and word_index >= len(session['medium_words']):
        session['difficulty'] = 'hard'
        session['word_index'] = 0
        difficulty = 'hard'
        word_index = 0
    elif difficulty == 'hard' and word_index >= len(session['hard_words']):
        return render_template('game_over.html')

    total_words = len(session['easy_words']) + len(session['medium_words']) + len(session['hard_words'])

    if difficulty == 'easy':
        overall_word_index = word_index
        word = session['easy_words'][word_index]
    elif difficulty == 'medium':
        overall_word_index = len(session['easy_words']) + word_index
        word = session['medium_words'][word_index]
    else: # hard
        overall_word_index = len(session['easy_words']) + len(session['medium_words']) + word_index
        word = session['hard_words'][word_index]

    if is_scrambled:
        char_list = list(word)
        random.shuffle(char_list)
        scrambled = "".join(char_list)
        if scrambled == word:
            scrambled = word[1:] + word[0]
        display_word = scrambled.upper()
        color = '#de425b'
        print(Panel(f"[bold green]{word.upper()}[/bold green]", title="Answer", border_style="green"))
    else:
        display_word = word.upper()
        color = '#488f31'

    return render_template(
        'index.html',
        word=display_word,
        color=color,
        is_scrambled=is_scrambled,
        word_index=overall_word_index,
        total_words=total_words
    )


@app.route('/next')
def next_word():
    if 'difficulty' not in session:
        return redirect(url_for('home'))

    is_scrambled = session.get('is_scrambled', True)
    if is_scrambled:
        session['is_scrambled'] = False
    else:
        session['is_scrambled'] = True
        session['word_index'] += 1

    return redirect(url_for('home'))


@app.route('/restart')
def restart():
    # Clear the session to restart the game
    session.clear()
    return redirect(url_for('home'))


import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Scrambled Words web app.")
    parser.add_argument("--port", type=int, default=5000, help="The port to run the web app on.")
    args = parser.parse_args()
    app.run(debug=True, port=args.port)
