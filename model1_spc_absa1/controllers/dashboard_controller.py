from flask import Blueprint, render_template, jsonify, request, make_response
from flask_login import login_required
from services.dashboard_service import DashboardService
from models.review import Review
from models.analysis_result import AnalysisResult
from database import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

def get_available_batches():
    """Mengambil batch_id unik yang memiliki data hasil klasifikasi, diurutkan berdasarkan tanggal ulasan paling baru"""
    batches = db.session.query(Review.batch_id)\
        .join(AnalysisResult, Review.id_review == AnalysisResult.id_review)\
        .filter(Review.batch_id.isnot(None))\
        .filter(AnalysisResult.sentiment_label.in_(['Positif', 'Negatif', 'Netral']))\
        .group_by(Review.batch_id)\
        .order_by(func.max(Review.created_at).desc())\
        .all()
    return [b[0] for b in batches if b[0]]

@dashboard_bp.route('/dashboard_analisis')
@login_required
def dashboard_page():
    """
    Merender halaman utama dashboard.
    Hanya mengambil data ringkasan untuk kartu di bagian atas.
    Data grafik akan diambil melalui API terpisah oleh JavaScript.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    time_grouping = request.args.get('time_grouping', 'harian')
    
    available_batches = get_available_batches()
    
    # Logika Default: Jika parameter batch_id tidak ada di URL (pertama kali buka), 
    # maka gunakan batch_id yang paling terbaru (index 0). 
    # Jika ada (termasuk jika nilainya kosong '' = Semua Batch), maka hormati pilihan tersebut.
    if 'batch_id' not in request.args and available_batches:
        batch_id = available_batches[0]
    else:
        batch_id = request.args.get('batch_id', '')
        
    # Konversi string angka menjadi integer agar cocok dengan tipe data kolom database
    if isinstance(batch_id, str) and batch_id.isdigit():
        batch_id = int(batch_id)

    service = DashboardService()
    all_data = service.get_dashboard_data(start_date, end_date, time_grouping, batch_id)
    return render_template('dashboard_analisis.html', summary=all_data['summary'], available_batches=available_batches, selected_batch=batch_id)

@dashboard_bp.route('/api/dashboard-data')
@login_required
def dashboard_api():
    """
    Menyediakan semua data yang diperlukan untuk grafik dashboard
    dalam format JSON.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    time_grouping = request.args.get('time_grouping', 'harian')
    
    if 'batch_id' not in request.args:
        available_batches = get_available_batches()
        batch_id = available_batches[0] if available_batches else ''
    else:
        batch_id = request.args.get('batch_id', '')
        
    # Konversi string angka menjadi integer agar cocok dengan tipe data kolom database
    if isinstance(batch_id, str) and batch_id.isdigit():
        batch_id = int(batch_id)

    service = DashboardService()
    chart_data = service.get_dashboard_data(start_date, end_date, time_grouping, batch_id)['charts']
    return jsonify(chart_data)