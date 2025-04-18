# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli-anahtar-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Veritabanı Modelleri
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    scores = db.relationship('Score', backref='user', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    topic = db.Column(db.String(100), nullable=False)

# Rotalar
@app.route('/')
def index():
    highest_score = None
    user_highest = None
    
    # En yüksek puanı al
    highest_score_record = Score.query.order_by(Score.score.desc()).first()
    if highest_score_record:
        highest_score = highest_score_record.score
    
    # Kullanıcının en yüksek puanını al
    if 'user_id' in session:
        user_highest_record = Score.query.filter_by(user_id=session['user_id']).order_by(Score.score.desc()).first()
        if user_highest_record:
            user_highest = user_highest_record.score
    
    return render_template('index.html', highest_score=highest_score, user_highest=user_highest)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Giriş başarılı!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            flash('Bu kullanıcı adı zaten kullanılıyor', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Kayıt başarılı! Lütfen giriş yapın.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Çıkış yaptınız', 'info')
    return redirect(url_for('index'))

@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        flash('Quiz\'e başlamak için lütfen giriş yapın', 'warning')
        return redirect(url_for('login'))
        
    # Soruları veritabanından çek
    questions = Question.query.all()
    
    # Eğer hiç soru yoksa, soruları ekle
    if not questions:
        questions = [
            Question(
                question_text="Discord bot geliştirmede Python'da kullanılan birincil kütüphane hangisidir?",
                option_a="discordpy",
                option_b="discord.py",
                option_c="pydiscord",
                option_d="botpy",
                correct_answer="b",
                topic="Chatbot automation with Python"
            ),
            Question(
                question_text="Flask'ta bir fonksiyonu bir URL'ye bağlamak için hangi dekoratör kullanılır?",
                option_a="@app.url()",
                option_b="@app.link()",
                option_c="@app.route()",
                option_d="@app.path()",
                correct_answer="c",
                topic="Web development with Python"
            ),
            Question(
                question_text="Aşağıdakilerden hangisi Python'da yapay zeka geliştirme kütüphanesi DEĞİLDİR?",
                option_a="TensorFlow",
                option_b="PyTorch",
                option_c="Scikit-learn",
                option_d="PyAI",
                correct_answer="d",
                topic="Artificial intelligence development with Python"
            ),
            Question(
                question_text="TensorFlow'da görüntü ön işleme için yaygın olarak kullanılan fonksiyon hangisidir?",
                option_a="tf.image.resize()",
                option_b="tf.image.process()",
                option_c="tf.preprocess_image()",
                option_d="tf.cv.resize()",
                correct_answer="a",
                topic="Computer Vision"
            ),
            Question(
                question_text="Python kütüphaneleri bağlamında NLTK neyin kısaltmasıdır?",
                option_a="Natural Language Tool Kit",
                option_b="Natural Language Testing Kit",
                option_c="Natural Language Toolkit",
                option_d="Natural Language Training Kit",
                correct_answer="c",
                topic="Natural Language Processing"
            )
        ]
        
        for question in questions:
            db.session.add(question)
            
        db.session.commit()
        
        # Soruları yeniden çek
        questions = Question.query.all()
    
    highest_score = None
    user_highest = None
    
    # En yüksek puanı al
    highest_score_record = Score.query.order_by(Score.score.desc()).first()
    if highest_score_record:
        highest_score = highest_score_record.score
    
    # Kullanıcının en yüksek puanını al
    user_highest_record = Score.query.filter_by(user_id=session['user_id']).order_by(Score.score.desc()).first()
    if user_highest_record:
        user_highest = user_highest_record.score
    
    return render_template('quiz.html', questions=questions, highest_score=highest_score, user_highest=user_highest)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        flash('Quiz\'i göndermek için lütfen giriş yapın', 'warning')
        return redirect(url_for('login'))
    
    score = 0
    questions = Question.query.all()
    
    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        if user_answer == question.correct_answer:
            score += 1
    
    # Puanı kaydet
    new_score = Score(score=score, user_id=session['user_id'])
    db.session.add(new_score)
    db.session.commit()
    
    # Kullanıcının en yüksek puanını al
    user_highest = Score.query.filter_by(user_id=session['user_id']).order_by(Score.score.desc()).first().score
    
    return render_template('results.html', 
                          score=score, 
                          total=len(questions), 
                          user_highest=user_highest)

@app.route('/initialize_db')
def initialize_db():
    # Tabloları oluştur
    with app.app_context():
        db.create_all()
        
        # Sadece soru yoksa ekle
        if Question.query.count() == 0:
            questions = [
                Question(
                    question_text="Discord bot geliştirmede Python'da kullanılan birincil kütüphane hangisidir?",
                    option_a="discordpy",
                    option_b="discord.py",
                    option_c="pydiscord",
                    option_d="botpy",
                    correct_answer="b",
                    topic="Chatbot automation with Python"
                ),
                Question(
                    question_text="Flask'ta bir fonksiyonu bir URL'ye bağlamak için hangi dekoratör kullanılır?",
                    option_a="@app.url()",
                    option_b="@app.link()",
                    option_c="@app.route()",
                    option_d="@app.path()",
                    correct_answer="c",
                    topic="Web development with Python"
                ),
                Question(
                    question_text="Aşağıdakilerden hangisi Python'da yapay zeka geliştirme kütüphanesi DEĞİLDİR?",
                    option_a="TensorFlow",
                    option_b="PyTorch",
                    option_c="Scikit-learn",
                    option_d="PyAI",
                    correct_answer="d",
                    topic="Artificial intelligence development with Python"
                ),
                Question(
                    question_text="TensorFlow'da görüntü ön işleme için yaygın olarak kullanılan fonksiyon hangisidir?",
                    option_a="tf.image.resize()",
                    option_b="tf.image.process()",
                    option_c="tf.preprocess_image()",
                    option_d="tf.cv.resize()",
                    correct_answer="a",
                    topic="Computer Vision"
                ),
                Question(
                    question_text="Python kütüphaneleri bağlamında NLTK neyin kısaltmasıdır?",
                    option_a="Natural Language Tool Kit",
                    option_b="Natural Language Testing Kit",
                    option_c="Natural Language Toolkit",
                    option_d="Natural Language Training Kit",
                    correct_answer="c",
                    topic="Natural Language Processing"
                )
            ]
            
            for question in questions:
                db.session.add(question)
                
            db.session.commit()
            
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)