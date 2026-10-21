import json
from datetime import datetime
import torch
import numpy as np
from utils.text_highlight_utils import generate_highlighted_html
from database import db 
from services.inference_service import get_saliency_explanation
from models.analysis_result import AnalysisResult

class InterpretationService:
    def enrich_with_interpretations(self, detail_data):
        """
        Memperkaya objek data detail laporan dengan HTML highlight 
        serta penjelasan per kata (XAI) secara efisien lewat caching database.
        """
        review_text = detail_data['review'].review_text
        review_id = detail_data['review'].id_review
        
        for analysis in detail_data['analysis']:
            # Hanya interpretasi ketika aspek terdeteksi (Mentioned == 1)
            if analysis.get('aspect_label', 0) != 1:
                continue
                
            # Cari object dari database untuk mengecek cache
            db_analysis = db.session.query(AnalysisResult).filter_by(
                id_review=review_id, 
                aspect_category=analysis['aspect']
            ).first()
            
            if db_analysis:
                # Cek eksistensi cache kata kunci langsung dari kolom database yang valid
                if db_analysis.lime_explanation and db_analysis.lime_explanation != "[]":
                    # Jika sudah di-cache di database, parse langsung
                    if isinstance(db_analysis.lime_explanation, str):
                        analysis['xai_explanation'] = json.loads(db_analysis.lime_explanation)
                    else:
                        analysis['xai_explanation'] = db_analysis.lime_explanation
                        
                    analysis['keywords'] = [item['word'] for item in analysis['xai_explanation']] if analysis.get('xai_explanation') else []
                    # Generate HTML highlight secara langsung tanpa perlu memanggil dari database
                    analysis['highlighted_review'] = generate_highlighted_html(review_text, analysis['xai_explanation'])
                    
                    # Cek apakah cache memiliki warna yang melenceng/salah 
                    # (misal: warna netral pada ulasan bersentimen Positif/Negatif)
                    is_invalid_cache = False
                    if analysis['sentiment'] in ['Positif', 'Negatif'] and analysis['xai_explanation']:
                        if any(item.get('sentiment') == 'neutral' for item in analysis['xai_explanation']):
                            is_invalid_cache = True
                            
                    # Jika hasil cache valid dan warnanya benar, jalankan mode CEPAT (Cache).
                    # Jika cache invalid, lanjutkan ke bawah untuk dihitung ulang dengan benar.
                    if analysis['xai_explanation'] and not is_invalid_cache:
                        continue
                
            # Apabila belum pernah diinterpretasi, jalankan proses Gradient Saliency
            try:
                explanation_data = get_saliency_explanation(review_text, analysis['aspect'], analysis['sentiment'])
                highlighted_html = generate_highlighted_html(review_text, explanation_data)
                
                if db_analysis:
                    db_analysis.lime_explanation = json.dumps(explanation_data) # Kolom database tetap lime_explanation untuk cegah error DB
                    db.session.commit()
                
                analysis['xai_explanation'] = explanation_data
                analysis['keywords'] = [item['word'] for item in explanation_data] if explanation_data else []
                analysis['highlighted_review'] = highlighted_html
            except Exception as e:
                print(f"Error memproses XAI: {e}")
                analysis['highlighted_review'] = review_text
                analysis['xai_explanation'] = []
                # Tampilkan pesan error di UI sebagai fallback agar lebih mudah di-debug
                analysis['keywords'] = [f"Err: {str(e)[:25]}"]
                
        return detail_data