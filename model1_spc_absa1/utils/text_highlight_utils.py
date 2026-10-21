import re
import html

def generate_highlighted_html(text, explanation_data):
    """
    Fungsi untuk memasukkan highlight HTML secara aman ke teks asli 
    berdasarkan kata-kata penting yang teridentifikasi oleh LIME.
    """
    if not explanation_data:
        return html.escape(text)
        
    word_data_map = {item["word"].lower(): item for item in explanation_data}
    
    def replace_match(match):
        word = match.group(0)
        word_lower = word.lower()
        
        if word_lower in word_data_map:
            data = word_data_map[word_lower]
            
            if data["sentiment"] == "positive":
                css_class = "bg-success bg-opacity-25 text-success fw-bold px-1 rounded"
            elif data["sentiment"] == "negative":
                css_class = "bg-danger bg-opacity-25 text-danger fw-bold px-1 rounded"
            else:
                css_class = "bg-secondary bg-opacity-25 text-secondary fw-bold px-1 rounded"
                
            escaped_word = html.escape(word)
            return f'<span class="{css_class}">{escaped_word}</span>'
            
        return html.escape(word)
        
    # Regex menggunakan word-boundary (aman untuk punctuation dan case-insensitivity)
    pattern = re.compile(r'\b\w+\b')
    result = []
    last_end = 0
    for match in pattern.finditer(text):
        result.append(html.escape(text[last_end:match.start()]))
        result.append(replace_match(match))
        last_end = match.end()
        
    result.append(html.escape(text[last_end:]))
    return "".join(result)