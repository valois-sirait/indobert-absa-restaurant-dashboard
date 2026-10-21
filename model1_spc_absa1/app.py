from flask import Flask

from flask_login import LoginManager
from werkzeug.security import generate_password_hash
# Import object db dan model
from database import db
from models.user import User
from models.review import Review
from models.analysis_result import AnalysisResult
from models.scraping_log import ScrapingLog
from models.csv_upload_log import CsvUploadLog
# Import blueprint dari file controllers/auth.py
from controllers.auth import auth_bp
from controllers.main_controller import main_bp
from controllers.data_controller import data_bp
from controllers.analysis import analysis_bp
from controllers.dashboard_controller import dashboard_bp
from controllers.report_controller import report_bp

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+pymysql://root:@localhost/absa?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'spc-absa-super-secret-key-12345'

# Menghubungkan aplikasi Flask dengan object SQLAlchemy
db.init_app(app)

# Konfigurasi Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Silakan login terlebih dahulu untuk mengakses halaman ini.'
login_manager.login_message_category = 'error'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    
    # Buat akun admin default (admin/admin) secara aman jika belum ada
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin')
        default_user = User(username='admin', password=hashed_pw)
        db.session.add(default_user)
        db.session.commit()

# Mendaftarkan blueprint auth ke aplikasi utama
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(data_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(report_bp)

if __name__ == "__main__":
    app.run(debug=True)
