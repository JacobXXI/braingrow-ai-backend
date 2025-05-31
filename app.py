from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from videodb import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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

if __name__ == '__main__':
    app.run(debug=True)