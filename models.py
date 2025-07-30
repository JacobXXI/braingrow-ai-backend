from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    tendency = db.Column(db.Text, nullable=True)
    photoUrl = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Video Model
class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(200), nullable=False)
    tags = db.Column(db.String(100), nullable=False)
    imageUrl = db.Column(db.String(200), nullable=False)
    
    def __repr__(self):
        return f"Video('{self.title}', '{self.description}', '{self.url}', '{self.tags}', '{self.imageUrl}')"

# Video Database Functions
def searchVideo(searchQuery: str, maxVideo: int):
    return Video.query.filter(
        db.or_(
            Video.title.like('%' + searchQuery + '%'),
            Video.tags.like('%' + searchQuery + '%')
        )
    ).limit(maxVideo).all()

def getRecommendedVideos(limit: int = 5):
    return Video.query.order_by(func.random()).limit(limit).all()

def getVideoById(video_id):
    return Video.query.filter_by(id=video_id).first()

def getAllVideos():
    return Video.query.all()

def addVideo(title, description, url, tags, imageUrl):
    try:
        video = Video(
            title=title,
            description=description,
            url=url,
            tags=tags,
            imageUrl=imageUrl
        )
        db.session.add(video)
        db.session.commit()
        return video
    except Exception as e:
        print(f"Error adding video: {e}")
        db.session.rollback()
        return None

# User Database Functions
def userLogin(username, password):
    try:
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            return user
        return None
    except Exception as e:
        print(f"Error in userLogin: {e}")
        return None

def userRegister(username, password, email=None):
    try:
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return None
        
        # Check if email already exists (if provided)
        if email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                return None
        
        # Create new user with hashed password
        hashed_password = generate_password_hash(password)
        user = User(
            username=username,
            password=hashed_password,
            email=email
        )
        
        db.session.add(user)
        db.session.commit()
        return user
    except Exception as e:
        print(f"Error in userRegister: {e}")
        db.session.rollback()
        return None

def userProfile(user_id):
    try:
        user = User.query.get(user_id)
        return user
    except Exception as e:
        print(f"Error in userProfile: {e}")
        return None