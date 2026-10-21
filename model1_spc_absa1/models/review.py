from database import db

class Review(db.Model):
    __tablename__ = 'reviews'

    id_review = db.Column(db.Integer, primary_key=True, autoincrement=True)
    source_id = db.Column(db.String(255), unique=True, nullable=False)
    batch_id = db.Column(db.String(50), nullable=True)
    input_source = db.Column(db.Enum('CSV', 'APIFY'), nullable=False)
    processing_status = db.Column(db.Enum('PENDING', 'COMPLETED', 'FAILED', 'SKIPPED'), default='PENDING')
    review_text = db.Column(db.Text, nullable=False)
    review_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Relasi ke tabel AnalysisResult (One-to-Many)
    analysis_results = db.relationship('AnalysisResult', backref='review', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Review {self.id_review} - {self.processing_status}>"