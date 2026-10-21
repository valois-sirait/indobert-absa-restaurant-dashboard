import csv
import io
import uuid
import hashlib
from datetime import datetime

def parse_csv_file(file_stream):
    """Parsing file CSV dan memetakan datanya."""
    stream = io.StringIO(file_stream.read().decode("UTF8"), newline=None)
    csv_input = csv.DictReader(stream)
    
    results = []
    
    stats = {
        "total_rows": 0,
        "empty_rows": 0
    }
    
    for row in csv_input:
        stats["total_rows"] += 1
        # Aturan 1: Ambil kolom teks ulasan (mendukung nama kolom 'text' atau 'review_text')
        text = row.get("text", row.get("review_text", ""))
        
        # Jika tidak ada teks ulasan atau teks hanya berisi spasi kosong, lewati baris ini
        if not text or not text.strip():
            stats["empty_rows"] += 1
            continue
            
        # Aturan 2: Ambil kolom tanggal (mendukung nama kolom 'date' atau 'review_date')
        date_str = row.get("date", row.get("review_date", ""))
        
        # Aturan 3: Coba parsing tanggal jika ada. Jika kosong/format salah, fallback ke tanggal hari ini.
        r_date = None
        if date_str and date_str.strip():
            date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"]
            for fmt in date_formats:
                try:
                    r_date = datetime.strptime(date_str.strip(), fmt).date()
                    break
                except ValueError:
                    continue
                    
        # Jika tidak ada kolom tanggal, atau format tidak dikenali, tetapkan ke tanggal hari ini (otomatis)
        if not r_date:
            r_date = datetime.today().date()

        # Cek apakah CSV memiliki kolom ID bawaan
        csv_id = row.get("id", row.get("review_id", row.get("source_id", "")))
        
        if csv_id and str(csv_id).strip():
            source_id = str(csv_id).strip()
        else:
            # Gunakan fungsi hash dari teks dan tanggal untuk menghasilkan ID yang unik namun deterministik
            # Hal ini mencegah data yang sama terduplikasi jika file di-upload ulang
            hash_input = f"{text.strip()}_{r_date}".encode('utf-8')
            source_id = f"CSV-{hashlib.md5(hash_input).hexdigest()[:15]}"

        results.append({
            "source_id": source_id,
            "review_text": text.strip(),
            "review_date": r_date
        })
    return results, stats