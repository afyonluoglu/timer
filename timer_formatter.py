import datetime

def format_time(total_seconds):
    """
    Kalan süreyi uygun formatta döndürür.
    1 saat ve üzeri için: saat:dakika:saniye
    1 saatten az için: dakika:saniye
    """
    if total_seconds >= 3600:  # 1 saat = 3600 saniye
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

# Kullanım örneği:
# remaining_seconds = 3665  # 1 saat 1 dakika 5 saniye
# formatted_time = format_time(remaining_seconds)
# print(formatted_time)  # Çıktı: 01:01:05

def get_current_datetime_string(format_str="%d-%m-%Y %H:%M:%S"):
    """
    Şu anki tarih ve saati belirtilen formatta bir string olarak döndürür.
    """
    return datetime.datetime.now().strftime(format_str)