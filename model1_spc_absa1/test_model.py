import torch
from services.inference_service import predict, get_saliency_explanation

ASPECTS = ["makanan", "pelayanan", "harga", "suasana", "lokasi"]
SENTIMENT_MAPPING = {
    0: "Negatif",
    1: "Netral",
    2: "Positif"
}

text = input("Masukkan teks ulasan: ")

print(f"\nText   : {text}")
print("-" * 50)

for aspect in ASPECTS:
    aspect_logits, sentiment_logits = predict(text, aspect)
    prob = torch.sigmoid(aspect_logits).item()
    
    if prob > 0.5:
        sentiment_idx = torch.argmax(sentiment_logits, dim=1).item()
        sentiment_label = SENTIMENT_MAPPING.get(sentiment_idx, "Netral")
        print(f"Aspek [{aspect.capitalize()}] : TERDETEKSI (Prob: {prob:.4f}) | Sentimen: {sentiment_label}")
        
        # Menambahkan penjelasan Saliency XAI
        explanation = get_saliency_explanation(text, aspect, sentiment_label)
        if explanation:
            print("  [XAI Explanation]:")
            for item in explanation:
                print(f"    - Kata: '{item['word']}', Bobot: {item['weight']:.4f}, Sentimen: {item['sentiment']}, Kekuatan: {item['strength']}")
        else:
            print("  [XAI Explanation]: Tidak ada kata kunci signifikan yang dihasilkan.")
    else:
        print(f"Aspek [{aspect.capitalize()}] : TIDAK TERDETEKSI (Prob: {prob:.4f})")