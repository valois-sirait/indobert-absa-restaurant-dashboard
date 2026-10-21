
from flask import Blueprint, request, jsonify, render_template, abort
from flask_login import login_required
from services.csv_service import parse_csv_file
from services.scraping_service import scrape_and_format_reviews
from services.review_service import save_reviews_to_db
from utils.validators import is_valid_csv, is_valid_url
from database import db
from models.review import Review
from models.analysis_result import AnalysisResult
from models.scraping_log import ScrapingLog
from models.csv_upload_log import CsvUploadLog

data_bp = Blueprint('data', __name__)

@data_bp.route("/upload_csv", methods=["POST"])
@login_required
def upload_csv():
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "Tidak ada file yang diunggah"}), 400
    
    file = request.files['file']
    if file.filename == '' or not is_valid_csv(file.filename):
        return jsonify({"success": False, "message": "File CSV tidak valid"}), 400

    try:
        parsed_data, stats = parse_csv_file(file.stream)
        saved_count, batch_id = save_reviews_to_db(parsed_data, batch_prefix="CSV", input_source="CSV")
        
        duplicate_count = len(parsed_data) - saved_count
        
        # Simpan riwayat eksekusi ke CsvUploadLog
        new_log = CsvUploadLog(
            batch_id=batch_id,
            filename=file.filename,
            total_rows=stats['total_rows'],
            empty_rows=stats['empty_rows'],
            duplicate_in_db=duplicate_count,
            saved_count=saved_count
        )
        db.session.add(new_log)
        db.session.commit()
        
        message = (
            f"✨ <b>Proses Unggah Selesai!</b><br><br>"
            f"✅ <b>{saved_count}</b> ulasan baru berhasil disimpan ke sistem.<br>"
            f"ℹ️ <b>{duplicate_count}</b> ulasan dilewati karena sudah ada sebelumnya.<br>"
            f"⚠️ <b>{stats['empty_rows']}</b> baris dilewati karena kosong."
        )
        return jsonify({"success": True, "message": message, "saved_count": saved_count})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@data_bp.route("/trigger_scraping", methods=["POST"])
@login_required
def trigger_scraping():
    # Mendukung pengambilan data dari JSON (Fetch API) maupun Form URL-Encoded biasa
    data = request.get_json(silent=True) or request.form
    url = data.get("url", "").strip()
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    
    # Ambil limit dari request frontend (jika dikirim), jika tidak, gunakan limit 100
    max_reviews_limit = int(data.get("max_reviews", 50))
    
    if not url or not is_valid_url(url):
        return jsonify({"success": False, "message": "URL Google Maps tidak valid. Pastikan link diawali dengan http:// atau https://"}), 400
        
    try:
        # Membuka ruang lebih besar (max_reviews) agar data lama tidak gagal terambil sebelum difilter
        scraped_data, stats = scrape_and_format_reviews(url, start_date, end_date, max_reviews=max_reviews_limit)
        saved_count, batch_id = save_reviews_to_db(scraped_data, batch_prefix="API", input_source="APIFY")
        
        # Hitung data ganda/terabaikan saat insert DB
        duplicate_count = len(scraped_data) - saved_count
        
        # Simpan riwayat eksekusi ke ScrapingLog
        new_log = ScrapingLog(
            batch_id=batch_id,
            url=url,
            filter_start_date=start_date if start_date else None,
            filter_end_date=end_date if end_date else None,
            total_fetched=stats['total_fetched'],
            no_text=stats['no_text'],
            out_of_date=stats['out_of_date'],
            duplicate_in_db=duplicate_count,
            saved_count=saved_count
        )
        db.session.add(new_log)
        db.session.commit()
        
        message = (
            f"✨ <b>Penarikan Data Selesai!</b><br><br>"
            f"✅ <b>{saved_count}</b> ulasan baru berhasil disimpan ke sistem.<br>"
            f"ℹ️ <b>{duplicate_count}</b> ulasan dilewati karena sudah ada sebelumnya.<br>"
            f"⚠️ <b>{stats['no_text']}</b> ulasan dilewati karena hanya berupa rating bintang (tanpa teks).<br>"
            f"📅 <b>{stats['out_of_date']}</b> ulasan dilewati karena di luar rentang tanggal yang dipilih."
        )
        
        return jsonify({"success": True, "message": message, "saved_count": saved_count})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@data_bp.route("/view_data/<string:review_id>")
@login_required
def view_data(review_id):
    review = Review.query.get(review_id)
    if not review:
        abort(404, description="Data ulasan tidak ditemukan")
    return render_template('manajemen_data_detail.html', review=review)

@data_bp.route("/delete_data/<string:review_id>", methods=["DELETE"])
@login_required
def delete_data(review_id):
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({"success": False, "message": "Data tidak ditemukan"}), 404
            
        # Hapus relasi hasil analisis terlebih dahulu jika ada
        AnalysisResult.query.filter_by(id_review=review_id).delete()
        db.session.delete(review)
        db.session.commit()
        return jsonify({"success": True, "message": "Data berhasil dihapus."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500