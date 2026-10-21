from flask import Blueprint, render_template, request, abort
from flask_login import login_required
from services.report_service import ReportService
from services.interpretation_service import InterpretationService
from database import db
from models.review import Review
from sqlalchemy import func
from models.csv_upload_log import CsvUploadLog
from models.scraping_log import ScrapingLog

report_bp = Blueprint('report', __name__)
report_service = ReportService()
interpretation_service = InterpretationService()

@report_bp.route('/laporan_detail')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    aspect = request.args.get('aspect', 'Semua Aspek')
    sentiment = request.args.get('sentiment', 'Semua Sentimen')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    batch_id = request.args.get('batch_id', '')

    if batch_id:
        # Jalur 1: Menampilkan tabel detail untuk batch_id yang spesifik.
        pagination, report_items = report_service.get_paginated_reports(
            page=page, per_page=10, search=search,
            aspect=aspect, sentiment=sentiment,
            start_date=start_date, end_date=end_date,
            batch_id=batch_id
        )
        return render_template('laporan_detail.html',
                               pagination=pagination,
                               items=report_items)
    else:
        # Jalur 2: Menampilkan grid ringkasan semua batch yang tersedia.
        
        # Ambil daftar semua batch untuk dropdown
        all_batches_query = db.session.query(Review.batch_id).filter(Review.batch_id.isnot(None)).group_by(Review.batch_id).order_by(func.max(Review.created_at).desc()).all()
        all_batches = [b[0] for b in all_batches_query if b[0]]

        # Query ini mengambil ringkasan data per batch: ID, jumlah ulasan, dan tanggal terbaru.
        batch_summary_query = db.session.query(
            Review.batch_id,
            func.count(Review.id_review).label('total_reviews'),
            func.max(Review.review_date).label('latest_date')
        ).filter(Review.batch_id.isnot(None))

        # Jika terdapat input pencarian pada halaman list batch, filter berdasarkan ID batch
        if search:
            batch_summary_query = batch_summary_query.filter(Review.batch_id == search)

        batch_summary_query = batch_summary_query.group_by(Review.batch_id)\
         .order_by(func.max(Review.created_at).desc())

        # Lakukan paginasi pada query ringkasan batch 
        pagination_for_batches = batch_summary_query.paginate(page=page, per_page=6, error_out=False)

        batch_summaries = []
        for b in pagination_for_batches.items:
            b_id = b.batch_id
            source_type = "Lainnya"
            source_detail = "-"
            total_fetched = 0
            saved_count = 0
            ignored_count = 0
            
            # Cari informasi detail dari tabel log berdasarkan batch_id
            csv_log = db.session.query(CsvUploadLog).filter_by(batch_id=b_id).first()
            if csv_log:
                source_type = "CSV"
                source_detail = csv_log.filename if hasattr(csv_log, 'filename') and csv_log.filename else 'File CSV'
                total_fetched = csv_log.total_rows if hasattr(csv_log, 'total_rows') else 0
                saved_count = csv_log.saved_count if hasattr(csv_log, 'saved_count') else 0
                ignored_count = (csv_log.empty_rows or 0) + (csv_log.duplicate_in_db or 0)
            else:
                scraping_log = db.session.query(ScrapingLog).filter_by(batch_id=b_id).first()
                if scraping_log:
                    source_type = "Scraping"
                    if hasattr(scraping_log, 'place_name') and scraping_log.place_name:
                        source_detail = scraping_log.place_name
                    elif hasattr(scraping_log, 'url') and scraping_log.url:
                        source_detail = scraping_log.url
                    else:
                        source_detail = 'Google Maps'
                    total_fetched = scraping_log.total_fetched if hasattr(scraping_log, 'total_fetched') else 0
                    saved_count = scraping_log.saved_count if hasattr(scraping_log, 'saved_count') else 0
                    ignored_count = (scraping_log.no_text or 0) + (scraping_log.out_of_date or 0) + (scraping_log.duplicate_in_db or 0)

            batch_summaries.append({
                'batch_id': b_id,
                'total_reviews': b.total_reviews,
                'latest_date': b.latest_date,
                'source_type': source_type,
                'source_detail': source_detail,
                'total_fetched': total_fetched,
                'saved_count': saved_count,
                'ignored_count': ignored_count
            })

        # Kirim hasil paginasi ke template
        return render_template('laporan_detail.html',
                               pagination=pagination_for_batches,
                               batch_summaries=batch_summaries,
                               all_batches=all_batches)

@report_bp.route('/laporan_detail/<string:review_id>')
@login_required
def detail(review_id):
    detail_data = report_service.get_review_detail(review_id)
    if not detail_data:
        abort(404, description="Review tidak ditemukan")
        
    # Enrikasi data dengan penjelasan fitur Explainable AI (LIME) per aspek
    detail_data = interpretation_service.enrich_with_interpretations(detail_data)
        
    return render_template('laporan_detail_item.html', data=detail_data)