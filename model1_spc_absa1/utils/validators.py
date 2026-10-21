def is_valid_csv(filename):
    """Mengecek apakah ekstensi file adalah csv."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

def is_valid_url(url):
    """Mengecek format URL secara sederhana."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    return url.startswith("http://") or url.startswith("https://")