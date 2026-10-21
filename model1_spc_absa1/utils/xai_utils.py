from lime.lime_text import LimeTextExplainer

# Inisialisasi secara global agar explainer tidak diload berulang kali
explainer = LimeTextExplainer(class_names=['Negatif', 'Netral', 'Positif'])

def generate_lime_explanation(text, aspect, predict_proba_fn, true_sentiment=None):
    """
    Fungsi untuk menghasilkan interpretasi sentimen dari LIME.
    :param text: Teks ulasan
    :param aspect: Aspek yang sedang dianalisis
    :param predict_proba_fn: Fungsi inferensi model global (menerima teks, mengembalikan probabilitas)
    :param true_sentiment: (Opsional) Hasil sentimen dari database agar penjelasan LIME konsisten
    """
    # Wrapper untuk mengikat (bind) variabel aspect ke fungsi inferensi batch
    def predictor(texts):
        return predict_proba_fn(texts, aspect)
    
    # Mapping sentimen asli ke indeks klasifikasi LIME
    sentiment_map = {'Negatif': 0, 'Netral': 1, 'Positif': 2}
    target_label = sentiment_map.get(true_sentiment) if true_sentiment else None
    
    # Proses penjelasan LIME (num_samples 100 cukup untuk menyeimbangkan kecepatan dan stabilitas)
    exp = explainer.explain_instance(
        text,
        predictor,
        labels=(target_label,) if target_label is not None else (1,),
        num_features=10,
        num_samples=100
    )
    
    if target_label is not None:
        predicted_label = target_label
        label_name = true_sentiment
    else:
        predicted_label = exp.available_labels()[0]
        label_name = explainer.class_names[predicted_label]
    
    # Ambil daftar fitur (kata) beserta nilai kepentingannya untuk label yang diprediksi
    features = exp.as_list(label=predicted_label)
    
    formatted_explanation = []
    stopwords = {"yang", "dan", "sih", "banget", "fyi", "dengan", "non", "di", "ke", "dari", "ini", "itu", "untuk", "yg", "nya", "sihh", "seperti", "ada", "pada", "juga"}
    
    for word, score in features:
        word_clean = word.strip().lower()
        if len(word_clean) <= 2 or not word_clean.isalnum() or word_clean in stopwords or word_clean.startswith("##"):
            continue
            
        # Hanya ambil kata yang MENDUKUNG prediksi label saat ini.
        # Jika score <= 0.01, berarti kata tersebut melawan prediksi atau tidak signifikan.
        if score < 0.01:
            continue
            
        sentiment = "positive" if label_name == 'Positif' else ("negative" if label_name == 'Negatif' else "neutral")
        strength = "strong" if score >= 0.2 else "normal"
        
        formatted_explanation.append({
            "word": word_clean,
            "sentiment": sentiment,
            "strength": strength,
            "weight": float(score)
        })
        
        if len(formatted_explanation) >= 8:
            break
        
    return formatted_explanation