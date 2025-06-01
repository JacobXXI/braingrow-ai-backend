from flask import Flask, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from videodb import *
from userdb import *
import jwt
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = "your-secret-key-here"  # Change this to a secure secret
db = SQLAlchemy(app)

@app.route('/')
def home():
    return "Hello, BrainGrow AI!"

@app.route('/search/<searchQuery>')
def search(searchQuery: str):
    videos = searchVideo(searchQuery)
    return jsonify([{
        'id': v.id,
        'title': v.title,
        'description': v.description,
        'url': v.url,
        'tags': v.tags,
        'imageUrl': v.imageUrl
    } for v in videos])

@app.route('/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'error': 'Authorization header missing'}), 401
        
    user = userLogin(auth.username, auth.password)
    if user:
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'user_id': user.id,
            'username': user.username
        })
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/profile')
def profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Authorization header missing'}), 401
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = userProfile(data['user_id'])
        if user:
            return jsonify({
                'user_id': user.id,
                'username': user.username,
                'tendency': user.tendency,
                'photoUrl': user.photoUrl
            }) 
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True)