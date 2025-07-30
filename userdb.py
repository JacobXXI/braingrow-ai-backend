from models import db

class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    tendency = db.Column(db.String(100), nullable=True)
    photoUrl = db.Column(db.String(100), nullable=True)
    def __repr__(self):
        return f"User('{self.username}', '{self.password}')"

def userLogin(username: str, password: str):
    user = user.query.filter_by(username=username).first()
    if user and user.password == password:
        return user
    return None

def userProfile(user_id: int):
    user = user.query.get(user_id)
    if user:
        return user
    return None