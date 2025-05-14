from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = '23jbgf822o3238rbh1o141r1hno8932gv238ef'  # Замените на ваш секретный ключ
NEWS_API_KEY = '9acec8a4a5e74ee38f1d3e37c56c9ee5'  # Замените на ваш API-ключ от NewsAPI

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('news.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создание таблиц в базе данных
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Главная страница с новостями
@app.route('/')
def index():
    conn = get_db_connection()
    news = conn.execute('SELECT * FROM news').fetchall()
    conn.close()
    return render_template('index.html', news=news)

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем уже существует.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

# Страница добавления новостей
@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        conn = get_db_connection()
        conn.execute('INSERT INTO news (title, content) VALUES (?, ?)', (title, content))
        conn.commit()
        conn.close()

        flash('Новость успешно добавлена!', 'success')
        return redirect(url_for('index'))

    return render_template('add_news.html')

# Загрузка новостей из NewsAPI
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Игнорируем предупреждения SSL
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


@app.route('/fetch_news')
def fetch_news():
    url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}'
    response = requests.get(url, verify=False)  # Отключаем проверку SSL
    data = response.json()

    if response.status_code == 200 and data.get('status') == 'ok':
        conn = get_db_connection()
        for article in data.get('articles', []):
            title = article.get('title', 'No Title')
            # Обработка поля description
            content = article.get('description')
            content = content.strip() if content is not None else 'No Content'

            # Проверяем, что title и content не пустые
            if title and content:
                try:
                    conn.execute('INSERT INTO news (title, content) VALUES (?, ?)', (title, content))
                except sqlite3.IntegrityError as e:
                    logging.error(f"Ошибка при сохранении новости: {e}")
                    continue

        conn.commit()
        conn.close()

        flash('Новости успешно загружены!', 'success')
    else:
        error_message = data.get('message', 'Неизвестная ошибка')
        flash(f'Ошибка при загрузке новостей: {error_message}', 'danger')

    return redirect(url_for('index'))


@app.route('/news')
def view_news():
    conn = get_db_connection()
    news = conn.execute('SELECT * FROM news').fetchall()
    conn.close()
    return render_template('view_news.html', news=news)


@app.route('/users')
def view_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('view_users.html', users=users)

# Запуск приложения
if __name__ == '__main__':
    init_db()  # Инициализация базы данных
    app.run(debug=True)