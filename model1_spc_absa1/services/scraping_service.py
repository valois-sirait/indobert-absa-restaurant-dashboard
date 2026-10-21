import uuid
from datetime import datetime
from utils.apify_client import fetch_google_reviews

def scrape_and_format_reviews(url, start_date_str=None, end_date_str=None, max_reviews=100):
    """Menarik data dari Apify Client, memfilter tanggal, dan memetakannya ke bentuk standard."""
    raw_items = fetch_google_reviews(url, max_reviews)
    
    # Ubah generator/iterable ke bentuk list agar bisa dihitung panjang datanya
    items = list(raw_items) if raw_items is not None else []
    results = []
    
    # Statistik untuk pelaporan dan log
    stats = {
        "total_fetched": len(items),
        "no_text": 0,
        "out_of_date": 0
    }

    # Konversi string tanggal dari frontend ke object datetime.date
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

    for item in items:
        # Lewati ulasan yang hanya memberikan bintang (tanpa teks)
        text = item.get("text")
        if not text or str(text).strip() == "":
            stats["no_text"] += 1
            continue
            
        review_date = item.get("publishedAtDate")
        if not review_date:
            stats["out_of_date"] += 1
            continue
            
        review_date_obj = datetime.fromisoformat(review_date[:10]).date()
        
        # Melakukan penyaringan berdasarkan tanggal yang dipilih
        if start_date and review_date_obj < start_date:
            stats["out_of_date"] += 1
            continue
        if end_date and review_date_obj > end_date:
            stats["out_of_date"] += 1
            continue

        source_id = item.get("reviewId") or item.get("id") or str(uuid.uuid4())
        results.append({ "source_id": source_id, "review_text": text, "review_date": review_date_obj })
    return results, stats