from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='submitter') 
    is_active = db.Column(db.Boolean, default=True) 

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_active(self):
        return self.is_active

    def __repr__(self):
        return f'<User {self.username}>'

class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)

    submitter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    submission_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    submitter = db.relationship('User', backref='ideas', lazy=True)

    @property
    def upvotes(self):
        return len([vote for vote in self.votes if vote.vote_type == 'upvote'])

    @property
    def downvotes(self):
        return len([vote for vote in self.votes if vote.vote_type == 'downvote'])
    
    def __repr__(self):
        return f'<Idea {self.title}>'

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey('idea.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vote_type = db.Column(db.String(10)) 

    def __repr__(self):
        return f'<Vote by User {self.user_id} on Idea {self.idea_id}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey('idea.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='selectin')  

    def __repr__(self):
        return f'<Comment {self.content[:20]}...>'


