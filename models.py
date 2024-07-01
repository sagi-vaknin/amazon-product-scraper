from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asin = db.Column(db.String(200), nullable=False)
    price_us = db.Column(db.String(200), nullable=True)
    link_us = db.Column(db.String(200), nullable=True)
    price_uk = db.Column(db.String(200), nullable=True)
    link_uk = db.Column(db.String(200), nullable=True)
    price_de = db.Column(db.String(200), nullable=True)
    link_de = db.Column(db.String(200), nullable=True)
    price_ca = db.Column(db.String(200), nullable=True)
    link_ca = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)