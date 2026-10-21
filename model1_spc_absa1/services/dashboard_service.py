import json
import ast
from sqlalchemy import func
from collections import defaultdict, Counter
from database import db
import re
from models.review import Review
from models.analysis_result import AnalysisResult

class DashboardService:
    """
    Service layer untuk menangani semua logika bisnis dan agregasi data
    yang dibutuhkan oleh halaman dashboard.
    """

    def get_dashboard_data(self, start_date=None, end_date=None, time_grouping='harian', batch_id=None):
        """
        Mengagregasi semua data yang diperlukan untuk dashboard dalam satu panggilan.
        Ini lebih efisien karena menghindari beberapa panggilan DB dari controller.
        """
        # Perbaiki rentang waktu agar mencakup jam 23:59:59 pada hari terakhir (end_date)
        # Mencegah data di hari terakhir terpotong karena defaultnya 00:00:00
        end_date_time = f"{end_date} 23:59:59" if end_date else None

        # 1. Ambil data ringkasan (summary cards)
        # Hanya hitung ulasan yang sudah memiliki hasil analisis (terklasifikasi valid)
        query_reviews = db.session.query(func.count(func.distinct(Review.id_review)))\
            .join(AnalysisResult, Review.id_review == AnalysisResult.id_review)\
            .filter(AnalysisResult.sentiment_label.in_(['Positif', 'Negatif', 'Netral']))

        if batch_id is not None and batch_id != '':
            query_reviews = query_reviews.filter(Review.batch_id == batch_id)
        if start_date:
            query_reviews = query_reviews.filter(Review.review_date >= start_date)
        if end_date:
            query_reviews = query_reviews.filter(Review.review_date <= end_date_time)
        total_reviews = query_reviews.scalar()

        # 2. Ambil distribusi sentimen global untuk Donut Chart & Skor Kepuasan
        sentiment_query_base = db.session.query(
            AnalysisResult.sentiment_label, 
            func.count(AnalysisResult.id_review)
        ).join(Review, AnalysisResult.id_review == Review.id_review)\
         .filter(AnalysisResult.sentiment_label.in_(['Positif', 'Negatif', 'Netral']))
        
        if batch_id is not None and batch_id != '':
            sentiment_query_base = sentiment_query_base.filter(Review.batch_id == batch_id)
        if start_date:
            sentiment_query_base = sentiment_query_base.filter(Review.review_date >= start_date)
        if end_date:
            sentiment_query_base = sentiment_query_base.filter(Review.review_date <= end_date_time)
            
        sentiment_query = sentiment_query_base.group_by(AnalysisResult.sentiment_label).all()
        
        sentiment_stats = {'Positif': 0, 'Negatif': 0, 'Netral': 0}
        total_sentiments = 0
        for label, count in sentiment_query:
            if label in sentiment_stats:
                sentiment_stats[label] = count
                total_sentiments += count
        
        satisfaction_score = 0
        if total_sentiments > 0:
            satisfaction_score = round((sentiment_stats.get('Positif', 0) / total_sentiments) * 100)

        # 3. Ambil data sentimen per aspek untuk Bar Chart
        aspect_query_base = db.session.query(
            AnalysisResult.aspect_category,
            AnalysisResult.sentiment_label,
            func.count(AnalysisResult.id_review)
        ).join(Review, AnalysisResult.id_review == Review.id_review)\
         .filter(AnalysisResult.sentiment_label.in_(['Positif', 'Negatif', 'Netral']))
        
        if batch_id is not None and batch_id != '':
            aspect_query_base = aspect_query_base.filter(Review.batch_id == batch_id)
        if start_date:
            aspect_query_base = aspect_query_base.filter(Review.review_date >= start_date)
        if end_date:
            aspect_query_base = aspect_query_base.filter(Review.review_date <= end_date_time)
            
        aspect_query = aspect_query_base.group_by(
            AnalysisResult.aspect_category,
            AnalysisResult.sentiment_label
        ).all()

        aspect_stats = defaultdict(lambda: {'Positif': 0, 'Negatif': 0, 'Netral': 0})
        for aspect, sentiment, count in aspect_query:
            if sentiment in ['Positif', 'Negatif', 'Netral']:
                aspect_stats[aspect][sentiment] += count
        
        # 4. Ambil data tren sentimen (time series) untuk Line Chart
        if time_grouping == 'mingguan':
            date_format_str = '%Y-W%U'
        elif time_grouping == 'bulanan':
            date_format_str = '%Y-%m'
        elif time_grouping == 'tahunan':
            date_format_str = '%Y'
        else:
            date_format_str = '%Y-%m-%d'
            
        time_series_query_base = db.session.query(
            func.date_format(Review.review_date, date_format_str).label('date_val'),
            AnalysisResult.sentiment_label,
            func.count(AnalysisResult.id_review)
        ).join(Review, AnalysisResult.id_review == Review.id_review)\
         .filter(AnalysisResult.sentiment_label.in_(['Positif', 'Negatif', 'Netral']))
        
        if batch_id is not None and batch_id != '':
            time_series_query_base = time_series_query_base.filter(Review.batch_id == batch_id)
        if start_date:
            time_series_query_base = time_series_query_base.filter(Review.review_date >= start_date)
        if end_date:
            time_series_query_base = time_series_query_base.filter(Review.review_date <= end_date_time)
            
        time_series_query = time_series_query_base.group_by('date_val', AnalysisResult.sentiment_label)\
         .order_by('date_val')\
         .all()

        time_series_stats = defaultdict(lambda: {'Positif': 0, 'Negatif': 0, 'Netral': 0})
        for date_val, sentiment, count in time_series_query:
            if sentiment in ['Positif', 'Negatif', 'Netral']:
                time_series_stats[date_val][sentiment] += count

        # 5. Global Insight Generation (Hybrid Strategy)
        # Pipeline: Cache XAI Saliency + Rule-based Aspect Proximity & Lexicon
        keyword_query_base = db.session.query(
            AnalysisResult.aspect_category,
            AnalysisResult.sentiment_label,
            Review.review_text,
            AnalysisResult.lime_explanation
        ).join(Review, AnalysisResult.id_review == Review.id_review)\
         .filter(AnalysisResult.sentiment_label.in_(['Positif', 'Negatif']))
         
        if batch_id is not None and batch_id != '':
            keyword_query_base = keyword_query_base.filter(Review.batch_id == batch_id)
        if start_date:
            keyword_query_base = keyword_query_base.filter(Review.review_date >= start_date)
        if end_date:
            keyword_query_base = keyword_query_base.filter(Review.review_date <= end_date_time)
            
        keyword_results = keyword_query_base.all()
        
        # Himpunan aturan filtering NLP ringan & Lexicon
        stopwords = {
            "yang", "dan", "sih", "banget", "fyi", "dengan", "di", "ke", "dari", 
            "ini", "itu", "untuk", "yg", "nya", "sihh", "seperti", "ada", "pada", 
            "juga", "saat", "aku", "saya", "kita", "kami", "adalah", "sebuah", 
            "aja", "buat", "karena", "kalau", "tapi", "akan", "cukup", "lumayan", 
            "sedikit", "lebih", "agak", "terasa", "begitu", "bisa", "dapat", 
            "perlu", "terus", "sudah", "telah", "saja", "masih", "pun", "dalam", 
            "bagi", "atau", "memang", "punya"
        }
        negations = {"tidak", "kurang", "gak", "nggak", "bukan", "jangan", "belum", "tak"}
        intensifiers = {"sangat", "terlalu", "paling", "sekali", "benar"}
        
        positive_words = {
            "enak", "empuk", "lezat", "ramah", "cepat", "bagus", "bersih", 
            "nyaman", "murah", "segar", "mantap", "lembut", "luas", "baik", 
            "puas", "keren", "manis", "gurih", "worth", "sebanding", "sesuai", 
            "sepadan", "responsif", "wajar", "masuk", "juara", "bersahabat", "meresap"
        }
        negative_words = {
            "mahal", "lama", "kotor", "dingin", "keras", "buruk", "lambat", 
            "bau", "kasar", "kurang", "asin", "pahit", "basi", "jelek", 
            "kecewa", "kacau", "parah", "lelet", "cuek", "bising", "berisik",
            "mahalnya", "kecil", "dikit", "kusam", "menyesal", "nyesal"
        }
        
        aspect_keywords = {
            'Makanan': {'makanan', 'rasa', 'daging', 'babi', 'panggang', 'sambal', 'porsi', 'menu', 'nasi', 'kuah', 'ayam', 'ikan', 'minum', 'kopi', 'teh', 'bumbu', 'bpk', 'kidu', 'kidu-kidu', 'arsik', 'bakmie', 'bumbunya', 'perbabian', 'kuliner'},
            'Layanan': {'pelayanan', 'pesanan', 'staf', 'waiter', 'kasir', 'waktu', 'datang', 'layanan', 'karyawan', 'pelayan', 'respon', 'satset', 'sat-set'},
            'Suasana': {'tempat', 'suasana', 'meja', 'kursi', 'ruangan', 'musik', 'ac', 'panas', 'bersih', 'toilet', 'kamar', 'dekorasi', 'area', 'hidden', 'gem', 'nyaman', 'ramai', 'sepi', 'tempatnya'},
            'Harga': {'harga', 'biaya', 'bayar', 'worth', 'sebanding', 'tagihan', 'pajak', 'promo', 'diskon', 'total', 'kantong', 'bersahabat'},
            'Lokasi': {'lokasi', 'akses', 'jalan', 'dekat', 'jauh', 'strategis', 'macet', 'tujuan', 'parkir', 'parkiran', 'alamat'}
        }
        
        # Menggunakan float (skor) sebagai ganti count
        keyword_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
        
        for aspect, sentiment, text, lime_explanation in keyword_results:
            if not text or sentiment not in ['Positif', 'Negatif']: 
                continue
                
            # 1. Parse cache saliency (XAI)
            saliency_dict = {}
            if lime_explanation:
                try:
                    explanations = json.loads(lime_explanation)
                    for item in explanations:
                        saliency_dict[item.get('word', '').lower()] = float(item.get('weight', 0.0))
                except Exception:
                    pass

            # 2. Rule-based extraction (Canonical Phrase Strategy)
            # Hilangkan angka untuk mencegah output teknis di UI
            clean_text = re.sub(r'[^a-zA-Z\s]', ' ', text.lower())
            tokens = clean_text.split()
            n_tokens = len(tokens)
            
            extracted_phrases = set()
            
            for i in range(n_tokens):
                w = tokens[i]
                # Anchor: Hanya Opinion Words (Adjective)
                is_lexicon_opinion = (sentiment == 'Positif' and w in positive_words) or \
                                     (sentiment == 'Negatif' and w in negative_words)
                is_saliency_opinion = (w in saliency_dict and saliency_dict.get(w, 0.0) > 0.35 and \
                                       w not in stopwords and w not in aspect_keywords.get(aspect, set()))
                
                if is_lexicon_opinion or is_saliency_opinion:
                    opinion_word = w
                    
                    # Normalisasi opinion word
                    if opinion_word.endswith("nya") and len(opinion_word) > 4:
                        opinion_word = opinion_word[:-3]
                        
                    # Deteksi modifier (intensifier atau negasi) sebelum opinion word
                    modifier = ""
                    if i > 0 and (tokens[i-1] in negations or tokens[i-1] in intensifiers):
                        modifier = tokens[i-1] + " "
                        
                    # Deteksi subject (aspect keyword) dalam radius +/- 4 kata
                    start = max(0, i - 4)
                    end = min(n_tokens, i + 5)
                    
                    subject = ""
                    # Prioritas 1: Aspect Lexicon
                    for j in range(start, end):
                        if j == i or (i > 0 and j == i-1 and modifier):
                            continue
                        cand = tokens[j]
                        if cand in aspect_keywords.get(aspect, set()):
                            subject = cand
                            # Gabungkan jika adjacent word juga aspect keyword (contoh: babi panggang)
                            if j + 1 < n_tokens and tokens[j+1] in aspect_keywords.get(aspect, set()) and j+1 != i:
                                subject = f"{cand} {tokens[j+1]}"
                            break
                            
                    # Prioritas 2: Saliency Noun (jika aspect tidak ditemukan eksplisit)
                    if not subject:
                        for j in range(start, end):
                            if j == i or (i > 0 and j == i-1 and modifier):
                                continue
                            cand = tokens[j]
                            if cand in saliency_dict and saliency_dict[cand] > 0.35 and \
                               cand not in stopwords and cand not in positive_words and \
                               cand not in negative_words and len(cand) > 2:
                                subject = cand
                                break
                    
                    # Normalisasi subject (hilangkan 'nya')
                    if subject and subject.endswith("nya") and len(subject) > 4:
                        subject = subject[:-3]

                    # Bentuk Canonical Phrase
                    if subject:
                        phrase = f"{subject} {modifier}{opinion_word}".strip()
                    else:
                        phrase = f"{modifier}{opinion_word}".strip()
                        
                    # Filter panjang phrase (harus 2-4 kata untuk menjamin makna penuh)
                    word_count = len(phrase.split())
                    if 2 <= word_count <= 4:
                        sal_scores = [saliency_dict.get(t, 0.0) for t in phrase.split()]
                        saliency_score = max(sal_scores) if sal_scores else 0.0
                        
                        extracted_phrases.add((phrase, saliency_score, is_lexicon_opinion, bool(subject)))
            
            # 3. Hybrid Scoring & Canonical Aggregation
            for phrase, sal_score, has_lexicon, has_aspect in extracted_phrases:
                rule_based_score = 0.0
                if has_lexicon: rule_based_score += 0.5
                if has_aspect: rule_based_score += 0.5
                elif len(phrase.split()) > 1: rule_based_score += 0.2
                    
                final_score = (0.7 * sal_score) + (0.3 * rule_based_score)
                
                # Threshold stabilisasi agar noise minor diabaikan
                if final_score > 0.15:
                    keyword_stats[aspect][sentiment][phrase] += final_score
                
        # Format menjadi top 5 kata kunci teratas per aspek dan sentimen
        # Karena memakai hybrid float score, kita sortir key berdasarkan nilainya
        top_keywords = {}
        for aspect, sentiments in keyword_stats.items():
            top_keywords[aspect] = {}
            for sentiment, phrases_dict in sentiments.items():
                # Ambil 5 teratas berdasarkan akumulasi final_score
                sorted_phrases = sorted(phrases_dict.items(), key=lambda x: x[1], reverse=True)[:5]
                # Format ke 'count' agar compatible dengan UI JS
                top_keywords[aspect][sentiment] = [{'word': w, 'count': round(score, 2)} for w, score in sorted_phrases]

        return {
            'summary': {
                'total_reviews': total_reviews,
                'satisfaction_score': satisfaction_score
            },
            'charts': {
                'sentiment_distribution': sentiment_stats,
                'aspect_sentiment': dict(aspect_stats),
                'time_series': dict(time_series_stats),
                'top_keywords': top_keywords  # Bypass jika controller membuang struktur 'insights'
            },
            'insights': {
                'top_keywords': top_keywords
            }
        }