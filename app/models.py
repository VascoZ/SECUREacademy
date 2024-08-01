from flask_login import UserMixin
from app import db
from datetime import datetime

# Association Table for many-to-many relationship
user_question_association = db.Table('user_question_association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id', ondelete='CASCADE')),
    db.Column('completion_time', db.DateTime, default=datetime.utcnow)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    completed_questions = db.relationship('Question', secondary=user_question_association, back_populates='completed_by', cascade='all, delete-orphan', single_parent=True)

    def get_id(self):
        return str(self.id)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal = db.Column(db.String(255), nullable=False)
    source_code = db.Column(db.Text, nullable=True)
    solving_material = db.Column(db.Text, nullable=True)

    completed_by = db.relationship('User', secondary=user_question_association, back_populates='completed_questions', cascade='all, delete-orphan', single_parent=True)
