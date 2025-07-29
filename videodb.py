from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(200), nullable=False)
    tags = db.Column(db.String(100), nullable=False)
    imageUrl = db.Column(db.String(200), nullable=False)
    def __repr__(self):
        return f"Video('{self.title}', '{self.description}', '{self.url}', '{self.tags}', '{self.imageUrl}')"

def searchVideo(searchQuery: str):
    return video.query.filter(
        db.or_(
            video.title.like('%' + searchQuery + '%'),
            video.tags.like('%' + searchQuery + '%')
        )
    ).all()

def getVideoById(video_id):
    return video.query.filter_by(id=video_id).first()