from database import db
from models.review import Review
import uuid
from datetime import datetime

def save_reviews_to_db(reviews_data, batch_prefix, input_source):
    """Menyimpan dictionary data ke dalam tabel Review menggunakan SQLAlchemy."""
    batch_id = f"DS-{batch_prefix}-{uuid.uuid4().hex[:6].upper()}"
    saved_count = 0
    
    for item in reviews_data:
        source_id = item.get("source_id") or f"{input_source}-{uuid.uuid4().hex[:10]}"
            
        existing = Review.query.filter_by(source_id=source_id).first()
        if not existing:
            new_review = Review(
                source_id=source_id, batch_id=batch_id, input_source=input_source,
                processing_status='PENDING', review_text=item.get("review_text", ""), 
                review_date=item.get("review_date", datetime.today().date())
            )
            db.session.add(new_review)
            saved_count += 1
    db.session.commit()
    return saved_count, batch_id