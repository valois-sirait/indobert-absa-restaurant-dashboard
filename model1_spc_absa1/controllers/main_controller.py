from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from models.review import Review

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_page'))
    return redirect(url_for('auth.login'))

# @main_bp.route("/manajemen_data")
# def management_data():
#     reviews_data = Review.query.order_by(Review.created_at.desc()).all()
#     return render_template("manajemen_data.html", reviews=reviews_data)

@main_bp.route('/manajemen_data')
@login_required
def management_data():
    # 1. Ambil nomor halaman dari parameter URL (misal: ?page=2), default adalah 1
    page = request.args.get('page', 1, type=int)
    
    # 2. Ambil data dari database menggunakan paginasi (10 data per halaman)
    pagination = Review.query.order_by(Review.review_date.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # 3. Kirimkan objek 'pagination' ke template
    return render_template('manajemen_data.html', pagination=pagination)

@main_bp.route("/test_inference")
@login_required
def test_inference():
    return render_template("test_inference.html")

@main_bp.route("/base")
@login_required
def base():
    return render_template("base.html")
