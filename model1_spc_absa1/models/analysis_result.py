from database import db

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'

    id_result = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_review = db.Column(db.Integer, db.ForeignKey('reviews.id_review', ondelete='CASCADE'), nullable=False)
    aspect_category = db.Column(db.Enum('Makanan', 'Layanan', 'Suasana', 'Harga', 'Lokasi'), nullable=False)
    sentiment_label = db.Column(db.Enum('Positif', 'Negatif', 'Netral'), nullable=False)
    confidence_score = db.Column(db.Numeric(5, 4), nullable=True)
    lime_explanation = db.Column(db.JSON, nullable=True)
    analyzed_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    def __repr__(self):
        return f"<AnalysisResult {self.id_result} - {self.aspect_category}: {self.sentiment_label}>"