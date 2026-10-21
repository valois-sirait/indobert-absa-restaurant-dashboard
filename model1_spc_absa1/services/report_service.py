from collections import defaultdict
from database import db
from models.review import Review
from models.analysis_result import AnalysisResult

class ReportService:
    def get_paginated_reports(self, page=1, per_page=10, search=None, aspect=None, sentiment=None, start_date=None, end_date=None, batch_id=None):
        """Mengambil data review dengan filter, sorting, dan pagination tanpa N+1 query."""
        query = db.session.query(Review)
        
        if search:
            query = query.filter(Review.review_text.ilike(f'%{search}%'))
        if start_date:
            query = query.filter(Review.review_date >= start_date)
        if end_date:
            query = query.filter(Review.review_date <= end_date)
        if batch_id:
            query = query.filter(Review.batch_id == batch_id)
            
        if aspect and aspect != 'Semua Aspek':
            query = query.filter(Review.id_review.in_(
                db.session.query(AnalysisResult.id_review).filter(AnalysisResult.aspect_category == aspect)
            ))
        if sentiment and sentiment != 'Semua Sentimen':
            query = query.filter(Review.id_review.in_(
                db.session.query(AnalysisResult.id_review).filter(AnalysisResult.sentiment_label == sentiment)
            ))
            
        query = query.order_by(Review.review_date.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Batch fetch analysis results untuk memecahkan N+1 Query Problem
        review_ids = [r.id_review for r in pagination.items]
        results = db.session.query(AnalysisResult).filter(AnalysisResult.id_review.in_(review_ids)).all()
        
        results_by_review = defaultdict(list)
        for res in results:
            results_by_review[res.id_review].append(res.sentiment_label)
            
        report_items = []
        for r in pagination.items:
            sents = results_by_review.get(r.id_review, [])
            total_aspek = len(sents)
            dominant = max(set(sents), key=sents.count) if sents else "-"
            
            report_items.append({
                'id_review': r.id_review,
                'review_text': r.review_text,
                'review_date': r.review_date,
                'total_aspek': total_aspek,
                'dominant_sentiment': dominant,
                'batch_id': r.batch_id
            })
            
        return pagination, report_items

    def get_review_detail(self, review_id):
        """Mengambil detail satu review beserta hasil per masing-masing 5 aspek."""
        review = db.session.query(Review).filter_by(id_review=review_id).first()
        if not review:
            return None
            
        results = db.session.query(AnalysisResult).filter_by(id_review=review_id).all()
        aspects = ["Makanan", "Layanan", "Suasana", "Harga", "Lokasi"]
        result_dict = {r.aspect_category: r.sentiment_label for r in results}
        
        analysis_table = []
        for asp in aspects:
            is_mentioned = 1 if asp in result_dict else 0
            analysis_table.append({
                'aspect': asp,
                'aspect_label': is_mentioned,
                'sentiment': result_dict.get(asp, '-')
            })
                
        return {'review': review, 'analysis': analysis_table}