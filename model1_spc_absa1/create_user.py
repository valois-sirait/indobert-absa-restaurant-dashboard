from app import app
from database import db
from models.user import User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("=== TAMBAH USER BARU ===")
    username = input("Masukkan username baru: ")
    
    # Cek apakah username sudah ada di database
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"\n[GAGAL] Username '{username}' sudah terdaftar! Silakan gunakan username lain.")
    else:
        password = input("Masukkan password baru: ")
        
        # Proses hashing password secara aman
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        
        db.session.add(new_user)
        db.session.commit()
        print(f"\n[SUKSES] User '{username}' berhasil dibuat! Silakan coba login.")