from datetime import datetime
from smartsync.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    contact_number = db.Column(db.String(15), unique=True, nullable=False)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
