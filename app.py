from flask import Flask, session, jsonify, request
from flask_session import Session
from flask_cors import CORS
import jwt
import datetime
import traceback

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
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/api/hello')
def hello():
    return {'message': 'Hello from Flask!'}

@app.route('/')
def home():
    return "Hello, BrainGrow AI!"

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
                'url': v.url,
                'tags': v.tags,
                'imageUrl': v.imageUrl
            }
            result.append(video_data)
        return jsonify(result)
            
    except Exception as e:
        print(f"Error in search route: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/<video_id>')
def get_video(video_id):
    try:
        video = getVideoById(video_id)
        if video:
            return jsonify({
                '_id': video.id,
                'title': video.title,
                'description': video.description,
                'author': 'Unknown',
                'date': datetime.datetime.now().isoformat(),
                'category': 'General',
                'views': 0,
                'likes': 0,
                'dislikes': 0,
                'url': video.url,
                'coverUrl': video.imageUrl
            })
        return jsonify({'error': 'Video not found'}), 404
    except Exception as e:
        print(f"Error in get_video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        auth = request.authorization
        if not auth and request.json:
            username = request.json.get('username')
            password = request.json.get('password')
        elif auth:
            username = auth.username
            password = auth.password
        else:
            return jsonify({'error': 'Username and password required'}), 401
            
        user = userLogin(username, password)
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
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
            return jsonify({
                'message': 'User created successfully',
                'user_id': user.id,
                'username': user.username
            }), 201
        return jsonify({'error': 'User creation failed'}), 400
    except Exception as e:
        print(f"Error in register: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile')
def profile():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authorization header missing'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = userProfile(data['user_id'])
        if user:
            return jsonify({
                'user_id': user.id,
                'username': user.username,
                'tendency': getattr(user, 'tendency', ''),
                'photoUrl': getattr(user, 'photoUrl', '')
            })
        return jsonify({'error': 'User not found'}), 404
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        print(f"Error in profile: {str(e)}")
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

if __name__ == '__main__':
    app.run(port=8080, debug=True)