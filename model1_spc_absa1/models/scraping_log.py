import uuid
from datetime import datetime
from database import db

class ScrapingLog(db.Model):
    __tablename__ = 'scraping_logs'
    
    id_log = db.Column(db.String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    batch_id = db.Column(db.String(50), nullable=False)
    url = db.Column(db.Text, nullable=False)
    
    # Parameter filter saat request dijalankan
    filter_start_date = db.Column(db.String(20), nullable=True)
    filter_end_date = db.Column(db.String(20), nullable=True)
    
    # Statistik hasil penarikan data
    total_fetched = db.Column(db.Integer, default=0)
    no_text = db.Column(db.Integer, default=0)
    out_of_date = db.Column(db.Integer, default=0)
    duplicate_in_db = db.Column(db.Integer, default=0)
    saved_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)