from flask import Flask, session, jsonify, request
from flask_session import Session
from flask_cors import CORS
import jwt
import datetime
import traceback
from functools import wraps

# Import everything from the consolidated models file
from models import (
    db, Video, User,
    searchVideo, getVideoById, addVideo,
    userLogin, userRegister, userProfile
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = "your-secret-key-here"

# Initialize extensions
db.init_app(app)
Session(app)

# Allow frontend origins with credentials support
CORS(app, origins=[
    "http://localhost:5174", 
    "http://localhost:5173",
    "https://localhost:3000"  # Added for your frontend auth endpoints
], supports_credentials=True)

# Create database tables
with app.app_context():
    db.create_all()

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for JWT token in Authorization header
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                request.current_user_id = data['user_id']
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired', 'code': 'TOKEN_EXPIRED'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401
        
        # Check for session-based login (fallback)
        if 'user_id' in session:
            request.current_user_id = session['user_id']
            return f(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401
    return decorated_function

@app.route('/api/hello')
def hello():
    return {'message': 'Hello from Flask!'}

@app.route('/')
def home():
    return "Hello, BrainGrow AI!"

# Updated search endpoint to match frontend expectations
@app.route('/api/search')
def search():
    try:
        searchQuery = request.args.get('query')
        print(f"Received search query: {searchQuery}")
        
        if not searchQuery:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        videos = searchVideo(searchQuery)
        print(f"Found {len(videos) if videos else 0} videos")
        
        if not videos:
            return jsonify([])
            
        result = []
        for v in videos:
            video_data = {
                'id': v.id,
                'title': v.title,
                'description': v.description,
                'creator': getattr(v, 'author', 'Unknown'),  # Frontend expects 'creator'
                'publishedAt': getattr(v, 'date', datetime.datetime.now()).isoformat(),
                'category': getattr(v, 'category', 'General'),
                'viewCount': getattr(v, 'views', 0),
                'likeCount': getattr(v, 'likes', 0),
                'dislikeCount': getattr(v, 'dislikes', 0),
                'videoUrl': v.url,  # Frontend expects 'videoUrl'
                'imageUrl': v.imageUrl
            }
            result.append(video_data)
        return jsonify(result)
            
    except Exception as e:
        print(f"Error in search route: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations')
def get_recommendations():
    limit = request.args.get('maxVideo', 5, type=int)
    videos = getRecommendedVideos(limit)
    return jsonify([{
        'id': v.id,
        'title': v.title,
        'description': v.description,
        'url': v.url,
        'tags': v.tags,
        'imageUrl': v.imageUrl
    } for v in videos])
        
@app.route('/api/video/<video_id>')
def get_video(video_id):
    try:
        video = getVideoById(video_id)
        if video:
            return jsonify({
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'creator': getattr(video, 'author', 'Unknown'),
                'publishedAt': getattr(video, 'date', datetime.datetime.now()).isoformat(),
                'category': getattr(video, 'category', 'General'),
                'viewCount': getattr(video, 'views', 0),
                'likeCount': getattr(video, 'likes', 0),
                'dislikeCount': getattr(video, 'dislikes', 0),
                'videoUrl': video.url,
                'coverUrl': video.imageUrl
            })
        return jsonify({'error': 'Video not found'}), 404
    except Exception as e:
        print(f"Error in get_video: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Updated login endpoint to handle email/password from frontend
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Frontend sends 'email' and 'password'
        email = data.get('email')
        password = data.get('password')
        remember_me = data.get('remember_me', False)
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        print(f"Login attempt for email: {email}")
        
        # Assuming userLogin can handle email instead of username
        # You might need to update your userLogin function to accept email
        user = userLogin(email, password)
        if user:
            # Store user session
            session['user_id'] = user.id
            session['username'] = getattr(user, 'username', user.email)
            session['logged_in'] = True
            session['login_time'] = datetime.datetime.now().isoformat()
            
            # Set session expiry based on remember_me
            if remember_me:
                session.permanent = True
                app.permanent_session_lifetime = datetime.timedelta(days=30)
                token_expiry = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            else:
                session.permanent = False
                token_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            
            # Create JWT token
            token = jwt.encode({
                'user_id': user.id,
                'username': getattr(user, 'username', user.email),
                'exp': token_expiry
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            print(f"User {email} logged in successfully at {session['login_time']}")
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user_id': user.id,
                'username': getattr(user, 'username', user.email),
                'logged_in': True,
                'login_time': session['login_time']
            })
        else:
            print(f"Failed login attempt for email: {email}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    try:
        username = session.get('username', 'Unknown')
        
        # Clear session data
        session.clear()
        
        print(f"User {username} logged out successfully")
        
        return jsonify({
            'message': 'Logout successful',
            'logged_in': False
        })
    except Exception as e:
        print(f"Error in logout: {str(e)}")
        return jsonify({'error': str(e)}), 500

# New signup endpoint to match frontend
@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
            
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
            
        # Create user with email as username if name not provided
        username = name if name else email.split('@')[0]
        
        user = userRegister(username, password, email)
        if user:
            # Auto-login after successful signup
            session['user_id'] = user.id
            session['username'] = user.username
            session['logged_in'] = True
            session['login_time'] = datetime.datetime.now().isoformat()
            
            # Create JWT token
            token_expiry = datetime.datetime.utcnow() + datetime.timedelta(days=7)
            token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'exp': token_expiry
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            print(f"New user registered and logged in: {email}")
            return jsonify({
                'message': 'User created successfully',
                'token': token,
                'user_id': user.id,
                'username': user.username
            }), 201
        return jsonify({'error': 'User creation failed - email may already exist'}), 400
    except Exception as e:
        print(f"Error in signup: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Video interaction endpoints
@app.route('/api/videos/<video_id>/like', methods=['POST'])
@login_required
def like_video(video_id):
    try:
        # Here you would implement like functionality
        # For now, returning mock data
        video = getVideoById(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Mock implementation - you'll need to add like functionality to your models
        new_likes = getattr(video, 'likes', 0) + 1
        
        return jsonify({
            'message': 'Video liked successfully',
            'likes': new_likes
        })
    except Exception as e:
        print(f"Error in like_video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/<video_id>/dislike', methods=['POST'])
@login_required
def dislike_video(video_id):
    try:
        # Here you would implement dislike functionality
        video = getVideoById(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Mock implementation - you'll need to add dislike functionality to your models
        new_dislikes = getattr(video, 'dislikes', 0) + 1
        
        return jsonify({
            'message': 'Video disliked successfully',
            'dislikes': new_dislikes
        })
    except Exception as e:
        print(f"Error in dislike_video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos/<video_id>/comments', methods=['POST'])
@login_required
def add_comment(video_id):
    try:
        data = request.json
        if not data or not data.get('text'):
            return jsonify({'error': 'Comment text required'}), 400
        
        video = getVideoById(video_id)
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        # Mock implementation - you'll need to add comment functionality to your models
        comment = {
            'id': 1,
            'text': data['text'],
            'user_id': request.current_user_id,
            'video_id': video_id,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment
        })
    except Exception as e:
        print(f"Error in add_comment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-auth')
def check_auth():
    """Check if user is currently authenticated"""
    try:
        # Check JWT token first
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                user = userProfile(data['user_id'])
                if user:
                    return jsonify({
                        'authenticated': True,
                        'user_id': user.id,
                        'username': getattr(user, 'username', user.email),
                        'login_method': 'token'
                    })
            except jwt.ExpiredSignatureError:
                return jsonify({'authenticated': False, 'error': 'Token expired'})
            except jwt.InvalidTokenError:
                return jsonify({'authenticated': False, 'error': 'Invalid token'})
        
        # Check session-based auth
        if 'user_id' in session and session.get('logged_in'):
            user = userProfile(session['user_id'])
            if user:
                return jsonify({
                    'authenticated': True,
                    'user_id': user.id,
                    'username': getattr(user, 'username', user.email),
                    'login_time': session.get('login_time'),
                    'login_method': 'session'
                })
        
        return jsonify({'authenticated': False})
        
    except Exception as e:
        print(f"Error in check_auth: {str(e)}")
        return jsonify({'authenticated': False, 'error': str(e)})

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
            
        user = userRegister(username, password, email)
        if user:
            print(f"New user registered: {username}")
            return jsonify({
                'message': 'User created successfully',
                'user_id': user.id,
                'username': user.username
            }), 201
        return jsonify({'error': 'User creation failed - username may already exist'}), 400
    except Exception as e:
        print(f"Error in register: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile')
@login_required
def profile():
    try:
        user = userProfile(request.current_user_id)
        if user:
            return jsonify({
                'user_id': user.id,
                'username': getattr(user, 'username', user.email),
                'email': getattr(user, 'email', ''),
                'tendency': getattr(user, 'tendency', ''),
                'photoUrl': getattr(user, 'photoUrl', ''),
                'session_info': {
                    'login_time': session.get('login_time'),
                    'session_permanent': session.permanent
                }
            })
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        print(f"Error in profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/protected-search')
@login_required
def protected_search():
    """Example of a protected route that requires login"""
    try:
        searchQuery = request.args.get('query')
        if not searchQuery:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # You can access the current user ID via request.current_user_id
        user = userProfile(request.current_user_id)
        videos = searchVideo(searchQuery)
        
        return jsonify({
            'user': getattr(user, 'username', user.email),
            'query': searchQuery,
            'results': [{
                'id': v.id,
                'title': v.title,
                'description': v.description,
                'creator': getattr(v, 'author', 'Unknown'),
                'publishedAt': getattr(v, 'date', datetime.datetime.now()).isoformat(),
                'category': getattr(v, 'category', 'General'),
                'viewCount': getattr(v, 'views', 0),
                'likeCount': getattr(v, 'likes', 0),
                'dislikeCount': getattr(v, 'dislikes', 0),
                'videoUrl': v.url,
                'imageUrl': v.imageUrl
            } for v in videos] if videos else []
        })
    except Exception as e:
        print(f"Error in protected_search: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-sample-data')
def add_sample_data():
    try:
        # Check if data already exists
        existing = Video.query.first()
        if existing:
            return jsonify({'message': 'Sample data already exists', 'count': Video.query.count()})
        
        # Add sample videos using the addVideo function
        sample_data = [
            ("Python Tutorial", "Learn Python programming basics", "https://youtube.com/watch?v=123", "python,programming,tutorial", "https://example.com/python.jpg"),
            ("Flask Web Development", "Build web applications with Flask", "https://youtube.com/watch?v=456", "flask,web,python", "https://example.com/flask.jpg"),
            ("JavaScript Basics", "Introduction to JavaScript programming", "https://youtube.com/watch?v=789", "javascript,web,frontend", "https://example.com/js.jpg")
        ]
        
        for title, description, url, tags, imageUrl in sample_data:
            addVideo(title, description, url, tags, imageUrl)
        
        return jsonify({'message': 'Sample data added successfully', 'count': len(sample_data)})
    except Exception as e:
        print(f"Error adding sample data: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Debug route to check current session
@app.route('/api/debug-session')
def debug_session():
    return jsonify({
        'session_data': dict(session),
        'session_permanent': session.permanent
    })

if __name__ == '__main__':
    app.run(port=8080, debug=True)