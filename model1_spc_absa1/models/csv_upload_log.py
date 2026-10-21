import uuid
from datetime import datetime
from database import db

class CsvUploadLog(db.Model):
    __tablename__ = 'csv_upload_logs'
    
    id_log = db.Column(db.String(50), primary_key=True, default=lambda: uuid.uuid4().hex)
    batch_id = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    
    total_rows = db.Column(db.Integer, default=0)
    empty_rows = db.Column(db.Integer, default=0)
    duplicate_in_db = db.Column(db.Integer, default=0)
    saved_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.now)