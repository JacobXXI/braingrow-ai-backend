from models import db  # Import the shared db instance

class Video(db.Model):  # Changed to capital V for consistency
    __tablename__ = 'videos'  # Explicitly set table name
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(200), nullable=False)
    tags = db.Column(db.String(100), nullable=False)
    imageUrl = db.Column(db.String(200), nullable=False)
    
    def __repr__(self):
        return f"Video('{self.title}', '{self.description}', '{self.url}', '{self.tags}', '{self.imageUrl}')"

def searchVideo(searchQuery: str):
    return Video.query.filter(
        db.or_(
            Video.title.like('%' + searchQuery + '%'),
            Video.tags.like('%' + searchQuery + '%')
        )
    ).all()

def getVideoById(video_id):
    return Video.query.filter_by(id=video_id).first()