import torch
import json
import re
import csv
import os

from datetime import datetime
from database import db
from models.review import Review
from models.analysis_result import AnalysisResult
from services.inference_service import predict, get_saliency_explanation

ASPECT_MAPPING = {
    "makanan": "Makanan",
    "pelayanan": "Layanan",
    "harga": "Harga",
    "suasana": "Suasana",
    "lokasi": "Lokasi"
}

SENTIMENT_MAPPING = {
    0: "Negatif",
    1: "Netral",
    2: "Positif"
}

# --- Inisialisasi Kamus Slang (Dijalankan sekali saat service dimuat) ---
SLANG_DICT = {}
try:
    print("=> Memuat kamus slang lokal...")
    SLANG_FILE_PATH = r"D:\model1_spc_absa\data\indo_slang_words.csv"
    
    if os.path.exists(SLANG_FILE_PATH):
        with open(SLANG_FILE_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row: continue
                
                if len(row) >= 2: # Jika CSV standar (kolom 1: slang, kolom 2: formal)
                    SLANG_DICT[row[0].strip()] = row[1].strip()
                elif len(row) == 1 and ':' in row[0]: # Jika format raw text "slang : formal"
                    parts = row[0].split(':', 1)
                    SLANG_DICT[parts[0].strip()] = parts[1].strip()
            
        excluded_words = ['bpk', 'karo', 'kidu']
        for word in excluded_words:
            if word in SLANG_DICT:
                del SLANG_DICT[word]
        print(f"=> Kamus slang berhasil dimuat! ({len(SLANG_DICT)} kata)")
    else:
        print(f"=> Peringatan: File kamus tidak ditemukan di {SLANG_FILE_PATH}")
except Exception as e:
    print(f"=> Peringatan: Gagal memuat kamus slang: {e}")

def clean_text(text):
    if not isinstance(text, str): return ""
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Di python asli, gunakan <.*?> bukan &lt;.*?&gt; yang merupakan format escape HTML
    text = re.sub(r'<.*?>', '', text) 
    text = re.sub(r'[^\w\s\.,!\?]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_text(text):
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    words = text.split()
    normalized_words = [SLANG_DICT.get(w.lower(), w) for w in words]
    return ' '.join(normalized_words)

def preprocess_for_inference(text):
    """Pre-processing disamakan dengan tahap pelatihan (cleaning & normalisasi slang)."""
    if not text: return ""
    text = clean_text(text)
    text = normalize_text(text)
    return text

def run_analysis():
    pending_reviews = Review.query.filter_by(processing_status='PENDING').all()
    # pending_reviews = Review.query.filter_by(processing_status='PENDING').limit(50).all()  
    
    if not pending_reviews:
        return {
            'success': True,
            'total_processed': 0,
            'failed': 0,
            'message': 'Tidak ada ulasan baru berstatus PENDING.'
        }

    processed_count = 0
    skipped_count = 0
    failed_count = 0

    for review in pending_reviews:
        try:
            text = review.review_text
            text = preprocess_for_inference(review.review_text)
            
            # Sama seperti pelatihan: filter jika teks < 3 karakter setelah di-clean
            if len(text) < 3:
                review.processing_status = 'SKIPPED'
                skipped_count += 1
                continue
            
            # Looping untuk Setiap Aspek
            for aspect_input, aspect_db_enum in ASPECT_MAPPING.items():
                
                # Memanggil Model Inference Service
                aspect_logits, sentiment_logits = predict(text, aspect_input)

                # Hitung Threshold Mentions & Label Sentimen
                aspect_prob = torch.sigmoid(aspect_logits).item()
                
                if aspect_prob > 0.5:
                    sentiment_idx = torch.argmax(sentiment_logits, dim=1).item()
                    sentiment_label = SENTIMENT_MAPPING.get(sentiment_idx, "Netral")

                    # Generate Saliency XAI secara langsung (Background caching)
                    explanation_data = get_saliency_explanation(text, aspect_input, sentiment_label)

                    # Simpan hasil analisis ke Database
                    new_result = AnalysisResult(
                        id_review=review.id_review,
                        aspect_category=aspect_db_enum,
                        sentiment_label=sentiment_label,
                        confidence_score=aspect_prob,
                        lime_explanation=json.dumps(explanation_data)
                    )
                    db.session.add(new_result)
            
            # Update status menjadi COMPLETED setelah selesai semua aspek
            review.processing_status = 'COMPLETED'
            processed_count += 1
            
        except Exception as e:
            print(f"Error memproses review {review.id_review}: {e}")
            review.processing_status = 'FAILED'
            failed_count += 1

    message = (
        f"🤖 <b>Proses Analisis AI Selesai!</b><br><br>"
        f"✅ <b>{processed_count}</b> ulasan berhasil dianalisis sentimennya.<br>"
        f"⚠️ <b>{skipped_count}</b> ulasan dilewati karena teks terlalu pendek atau tidak bermakna.<br>"
        f"❌ <b>{failed_count}</b> ulasan gagal diproses karena kesalahan sistem."
    )

    try:
        db.session.commit()
        return {
            'success': True,
            'total_classified': processed_count,
            'total_skipped': skipped_count,
            'failed': failed_count,
            'message': message
        }
    except Exception as e:
        db.session.rollback()
        raise e