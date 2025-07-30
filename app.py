from flask import Flask, session, jsonify, request
from flask_session import Session
from flask_cors import CORS
from videodb import searchVideo, getVideoById
from userdb import *
import jwt
import datetime
from models import db
import traceback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SECRET_KEY'] = "your-secret-key-here"  # Change this to a secure secret
db.init_app(app)

# Initialize Flask-Session
Session(app)

# Allow only frontend origin with credentials support
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
        print(f"Received search query: {searchQuery}")  # Debug log
        
        if not searchQuery:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Add detailed error handling for the search function
        try:
            videos = searchVideo(searchQuery)
            print(f"Found {len(videos) if videos else 0} videos")  # Debug log
        except Exception as search_error:
            print(f"Error in searchVideo function: {str(search_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Search function failed: {str(search_error)}'}), 500
        
        if not videos:
            return jsonify([])  # Return empty array if no videos found
            
        # Add error handling for video serialization
        try:
            result = []
            for v in videos:
                video_data = {
                    'id': getattr(v, 'id', None),
                    'title': getattr(v, 'title', 'No title'),
                    'description': getattr(v, 'description', 'No description'),
                    'url': getattr(v, 'url', ''),
                    'tags': getattr(v, 'tags', ''),
                    'imageUrl': getattr(v, 'imageUrl', '')
                }
                result.append(video_data)
            return jsonify(result)
        except Exception as serialize_error:
            print(f"Error serializing videos: {str(serialize_error)}")
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Video serialization failed: {str(serialize_error)}'}), 500
            
    except Exception as e:
        print(f"General error in search route: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/<video_id>')
def get_video(video_id):
    try:
        print(f"Getting video with ID: {video_id}")  # Debug log
        
        # Check if getVideoById function exists
        if 'getVideoById' not in globals():
            return jsonify({'error': 'getVideoById function not available'}), 500
            
        video = getVideoById(video_id)
        if video:
            return jsonify({
                '_id': getattr(video, 'id', video_id),
                'title': getattr(video, 'title', 'No title'),
                'description': getattr(video, 'description', 'No description'),
                'author': getattr(video, 'author', 'Unknown'),
                'date': getattr(video, 'date', datetime.datetime.now()).isoformat() if hasattr(video, 'date') else None,
                'category': getattr(video, 'category', 'General'),
                'views': getattr(video, 'views', 0),
                'likes': getattr(video, 'likes', 0),
                'dislikes': getattr(video, 'dislikes', 0),
                'url': getattr(video, 'url', ''),
                'coverUrl': getattr(video, 'imageUrl', '')
            })
        return jsonify({'error': 'Video not found'}), 404
    except Exception as e:
        print(f"Error in get_video: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        # Handle both Basic Auth and JSON body
        auth = request.authorization
        if not auth and request.json:
            # Handle JSON login
            username = request.json.get('username')
            password = request.json.get('password')
        elif auth:
            username = auth.username
            password = auth.password
        else:
            return jsonify({'error': 'Username and password required'}), 401
            
        print(f"Login attempt for username: {username}")  # Debug log
        
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
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        print(f"Registration attempt for username: {username}")  # Debug log
        
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
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile')
def profile():
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authorization header missing'}), 401
        
        # Handle Bearer token format
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
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=8080, debug=True)