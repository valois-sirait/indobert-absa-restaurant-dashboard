import os
import re
import torch
from transformers import AutoTokenizer, AutoModel
from model_ai.model_definition import MultiHeadIndoBERT

# --- KONFIGURASI PATH MODEL ---
LOCAL_BASE_MODEL_DIR = "model_ai/IndoBERT_Base_P1" 
MODEL_WEIGHT_PATH = "model_ai/IndoBERT_ABSA_Final_Ke2/multihead_absa_model.pt"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = None
tokenizer = None

def _load_model():
    global model, tokenizer
    if model is not None and tokenizer is not None:
        return

    print("=> Mempersiapkan Model IndoBERT ABSA (Inference Service)...")
    try:
        tokenizer_path = LOCAL_BASE_MODEL_DIR if os.path.exists(LOCAL_BASE_MODEL_DIR) else "indobenchmark/indobert-base-p1"
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        base_model = AutoModel.from_pretrained(tokenizer_path)

        model = MultiHeadIndoBERT(base_model)
        
        model.load_state_dict(torch.load(MODEL_WEIGHT_PATH, map_location=device))
        model.to(device)
        model.eval()
        print("=> Model berhasil di-load!")
    except Exception as e:
        print(f"=> ERROR load model: {e}")
        model = None
        tokenizer = None

# Eksekusi saat modul pertama kali di-import (Singleton behaviour)
_load_model()

def predict(text, aspect):
    if model is None or tokenizer is None:
        raise RuntimeError("Model AI belum di-load atau gagal di-load. Periksa konfigurasi.")

    inputs = tokenizer(
        text,
        aspect,
        return_tensors="pt",
        truncation=True,
        max_length=128,
        padding="max_length"
    ).to(device)

    with torch.no_grad():
        aspect_logits, sentiment_logits = model(
            input_ids=inputs['input_ids'],
            attention_mask=inputs['attention_mask']
        )

    return aspect_logits, sentiment_logits

def get_saliency_explanation(text, aspect, true_sentiment):
    """
    Metode XAI menggunakan 'Input x Gradient Saliency'. Ini secara matematis mengukur seberapa 
    besar kontribusi embedding kata terhadap logit prediksi tanpa noise Attention.
    """
    if model is None or tokenizer is None:
        return []

    # Pemetaan sentimen target
    sentiment_map = {'Negatif': 0, 'Netral': 1, 'Positif': 2}
    target_idx = sentiment_map.get(true_sentiment, 1)

    model.eval()
    
    # PENTING: Aktifkan gradient tracking untuk mengukur turunan (derivatives)
    with torch.set_grad_enabled(True):
        inputs = tokenizer(
            text,
            aspect,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding="max_length"
        ).to(device)

        input_ids = inputs['input_ids']
        attention_mask = inputs['attention_mask']

        # 1. Dapatkan word embeddings dari layer pertama secara manual
        embeddings = model.bert.embeddings.word_embeddings(input_ids)
        
        # 2. Pastikan tensor embeddings bertindak sebagai "leaf node" yang 
        #    menerima gradien (mengatasi issue list kosong jika layer model frozen)
        embeddings = embeddings.detach().clone()
        embeddings.requires_grad_(True)

        # 3. Forward pass men-inject embeddings langsung (bypass wrapper model)
        # Kita langsung memanggil model.bert seperti yang dilakukan di Google Colab
        outputs = model.bert(inputs_embeds=embeddings, attention_mask=attention_mask)
        cls_output = model.dropout(outputs.pooler_output)
        sentiment_logits = model.sentiment_head(cls_output)

        # 4. Ambil logit (skor mentah sebelum softmax) dari kelas target, lalu backward pass
        target_logit = sentiment_logits[0, target_idx]
        model.zero_grad()
        target_logit.backward()
        
        # Jaga-jaga jika gradient gagal dihitung (mencegah NoneType error)
        if embeddings.grad is None:
            return []

        # 5. Hitung Saliency (Pure Gradient Magnitude)
        # Menyamakan perhitungan persis dengan yang ada di Google Colab Anda
        saliency_scores = embeddings.grad[0].abs().sum(dim=-1).detach().cpu().numpy()
        saliency_scores = (saliency_scores - saliency_scores.min()) / (saliency_scores.max() - saliency_scores.min() + 1e-8)

    # 6. Pembersihan token & penyusunan untuk UI
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0].tolist())
    stopwords = {
        "yang", "dan", "sih", "banget", "fyi", "dengan", "non", "di", "ke", "dari", 
        "ini", "itu", "untuk", "yg", "nya", "sihh", "seperti", "ada", "pada", 
        "juga", "saat", "aku", "saya", "kita", "kami", "adalah", "sebuah", 
        "aja", "buat", "karena", "kalau", "tapi", "akan", "cukup", "lumayan", 
        "sedikit", "lebih", "agak", "terasa", "begitu", "bisa", "dapat", 
        "perlu", "terus", "sudah", "telah", "saja", "masih", "pun", "dalam", 
        "bagi", "atau", "memang", "punya", "semoga", "kedepan", "semakin", "jadi", "dgn",
        "tetapi", "sangat", "paling", "sekali", "benar", "cuma", "hanya", "namun", 
        "walau", "walaupun", "meski", "meskipun", "bahkan", "sehingga", "bahwa", 
        "lalu", "kemudian", "tetap", "tidak", "enggak", "nggak", "ga", "gak", "bukan",
        "belum", "jangan", "pokoknya", "jamin", "dijamin", "asli", "saranku", "saran",
        "kalian", "orang", "mau", "coba", "yogyakarta", "jogja", "sini", "sana", 
        "penting", "lah", "makin", "pakai", "pake", "beneran", "salah", "satu",
        "sampai", "berasa", "bikin", "banyak", "biar", "kasih", "dong", "deh", "kan",
        "buat", "apa", "si", "ya", "yaa", "kok"
    }
    
    # Lexicon untuk aspect-aware filtering
    ASPECT_LEXICON = {
        'Makanan': {'makanan', 'rasa', 'daging', 'babi', 'panggang', 'sambal', 'porsi', 'menu', 'nasi', 'kuah', 'ayam', 'ikan', 'minum', 'kopi', 'teh', 'bumbu', 'kecap', 'saos', 'saus', 'enak', 'lezat', 'gurih', 'empuk', 'manis', 'asin', 'pahit', 'keras', 'basi', 'dingin', 'segar', 'lauk', 'masakan', 'seafood', 'kualitas', 'kualitasnya', 'minuman', 'kue', 'roti', 'snack', 'rasanya', 'porsinya', 'dagingnya', 'kuahnya', 'makanannya', 'bakmie', 'bpk', 'kidu', 'arsik', 'bagus', 'mantap', 'oke', 'buruk', 'jelek', 'bumbunya', 'perbabian', 'kuliner', 'juara', 'meresap', 'wajib', 'dicoba'},
        'Layanan': {'pelayanan', 'pesanan', 'staf', 'waiter', 'kasir', 'waktu', 'datang', 'layanan', 'karyawan', 'pelayan', 'respon', 'cepat', 'lambat', 'lama', 'ramah', 'sopan', 'cuek', 'lelet', 'cekatan', 'sigap', 'baik', 'pelayanannya', 'stafnya', 'kasirnya', 'layanannya', 'kerjanya', 'bagus', 'mantap', 'oke', 'buruk', 'jelek', 'satset', 'sat-set'},
        'Suasana': {'tempat', 'suasana', 'meja', 'kursi', 'ruangan', 'musik', 'ac', 'panas', 'bersih', 'toilet', 'kamar', 'dekorasi', 'area', 'kotor', 'nyaman', 'bau', 'bising', 'berisik', 'luas', 'sempit', 'terang', 'gelap', 'dibersihkan', 'cuci', 'tangan', 'wastafel', 'tempatnya', 'suasananya', 'areanya', 'mejanya', 'kursinya', 'toiletnya', 'bagus', 'indah', 'rapi', 'estetik', 'mantap', 'oke', 'buruk', 'jelek', 'hidden', 'gem'},
        'Harga': {'harga', 'biaya', 'bayar', 'worth', 'sebanding', 'tagihan', 'pajak', 'promo', 'diskon', 'total', 'murah', 'mahal', 'wajar', 'pas', 'mahalnya', 'standart', 'harganya', 'bayarnya', 'biayanya', 'murahnya', 'struk', 'kembalian', 'price', 'pricey', 'oke', 'mantap', 'buruk', 'jelek', 'kantong', 'bersahabat'},
        'Lokasi': {'lokasi', 'akses', 'jalan', 'dekat', 'jauh', 'strategis', 'macet', 'tujuan', 'parkir', 'parkiran', 'alamat', 'mudah', 'sulit', 'terjangkau', 'juru', 'parkirannya', 'lokasinya', 'aksesnya', 'jalannya', 'bagus', 'oke', 'buruk', 'jelek'}
    }

    SENTIMENT_LEXICON = {
        'Positif': {'enak', 'lezat', 'gurih', 'empuk', 'segar', 'ramah', 'sopan', 'cepat', 'cekatan', 'baik', 'bersih', 'nyaman', 'luas', 'terang', 'bagus', 'indah', 'rapi', 'murah', 'worth', 'sepadan', 'wajar', 'mantap', 'keren', 'puas', 'kualitas', 'kualitasnya', 'oke', 'lumayan', 'estetik', 'pas', 'strategis', 'mudah', 'terjangkau', 'bersahabat', 'juara', 'nyaman', 'hidden', 'gem', 'meresap'},
        'Negatif': {'keras', 'basi', 'dingin', 'pahit', 'asin', 'lambat', 'lama', 'cuek', 'lelet', 'kotor', 'bau', 'bising', 'berisik', 'sempit', 'gelap', 'mahal', 'jelek', 'kecewa', 'parah', 'kacau', 'buruk', 'kasar', 'kurang', 'mahalnya', 'sulit', 'macet', 'jauh', 'pricey', 'menyesal', 'nyesal', 'buruk', 'gosong'}
    }

    aggregated_scores = {}
    
    # Temukan batas akhir teks ulasan asli (sebelum token [SEP] pertama)
    # Ini mencegah model mengekstrak kata dari kategori aspek yang disisipkan di akhir
    try:
        first_sep_idx = tokens.index("[SEP]")
    except ValueError:
        first_sep_idx = len(tokens)

    current_word = ""
    current_score = 0.0

    def process_accumulated_word(word, score):
        clean_w = re.sub(r'[^a-z0-9]', '', word.lower())
        # Hanya simpan kata valid, bukan stopword, dan yang benar-benar punya kontribusi Saliency POSITIF
        if len(clean_w) >= 2 and clean_w not in stopwords and score > 0:
            if clean_w not in aggregated_scores or score > aggregated_scores[clean_w]:
                aggregated_scores[clean_w] = score

    for i, token in enumerate(tokens):
        # Berhenti jika sudah mencapai bagian aspek atau mengabaikan padding
        if i >= first_sep_idx or token in ["[CLS]", "[SEP]", "[PAD]"] or attention_mask[0, i] == 0:
            continue
        
        score = float(saliency_scores[i])
        
        # Gabungkan subword (token yang berawalan ##) ke token sebelumnya (misal: "sou" + "##p" -> "soup")
        if token.startswith("##"):
            current_word += token.replace("##", "")
            current_score = max(current_score, score)
        else:
            if current_word:
                process_accumulated_word(current_word, current_score)
            
            # Mulai merakit kata baru
            current_word = token
            current_score = score
            
    # Jangan lupa simpan kata terakhir yang berada di akhir teks
    if current_word:
        process_accumulated_word(current_word, current_score)

    # 7. Pengurutan dan Prioritas (Valid secara Saintifik)
    # Urutkan secara murni berdasarkan skor Saliency asli dari model
    sorted_words = sorted(aggregated_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Mapping nama aspek dari input (huruf kecil) ke format key di ASPECT_LEXICON
    aspect_key_map = {
        "makanan": "Makanan",
        "pelayanan": "Layanan",
        "harga": "Harga",
        "suasana": "Suasana",
        "lokasi": "Lokasi"
    }
    mapped_aspect = aspect_key_map.get(aspect.lower(), aspect.capitalize())
    
    # Gunakan HANYA kamus spesifik untuk aspek ini (ASPECT_LEXICON).
    # Mencegah tercampurnya kata opini beda aspek (seperti 'ramah' masuk prioritas 'Makanan').
    target_relevant_words = ASPECT_LEXICON.get(mapped_aspect, set())

    final_keywords = []
    
    # Tahap 1: Utamakan max 2 kata yang relevan dengan aspek/sentimen, asalkan Saliency-nya ada
    for word, score in sorted_words:
        if word in target_relevant_words:
            final_keywords.append((word, score))
            if len(final_keywords) == 2:
                break

    # Tahap 2: Jika kata relevan kurang dari 2, isi sisanya dari ranking saliency tertinggi secara murni
    if len(final_keywords) < 2:
        for word, score in sorted_words:
            if not any(w == word for w, s in final_keywords):
                final_keywords.append((word, score))
                if len(final_keywords) == 2:
                    break
                    
    # Urutkan ulang 2 kata terpilih berdasarkan urutan skor yang sebenarnya
    final_keywords = sorted(final_keywords, key=lambda x: x[1], reverse=True)
    
    formatted_explanation = []
    if final_keywords:
        # Gunakan max_score global (dari kata nomor 1 model) agar skala normalisasi konsisten
        max_score = sorted_words[0][1] 
        for word, score in final_keywords:
            normalized_score = score / (max_score + 1e-9)
            
            sentiment = "positive" if true_sentiment == 'Positif' else ("negative" if true_sentiment == 'Negatif' else "neutral")
            strength = "strong" if normalized_score >= 0.5 else "normal"

            formatted_explanation.append({
                "word": word,
                "sentiment": sentiment,
                "strength": strength,
                "weight": normalized_score
            })

    return formatted_explanation