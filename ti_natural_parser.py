"""
Doğal dilde zamanlayıcı ve alarm komutlarını regex ve dateparser ile çözümleyen modül.
"""

import re
import datetime
import dateparser


def parse_natural_timer(text):
    """Doğal dilde alarm komutlarını gelişmiş şekilde analiz eden fonksiyon."""
    # 1. "X dakika/saat/gün sonra ..."
    match = re.search(r"(\d+)\s*(dakika|saat|gün)\s*sonra\s*(.*)", text, re.IGNORECASE)
    if match:
        print("✅ Match 1 found:", match.groups())

        value = int(match.group(1))
        unit = match.group(2).lower()
        aciklama = match.group(3).strip() or "Doğal Komut"
        if unit == "dakika":
            dakika = value
        elif unit == "saat":
            dakika = value * 60
        elif unit == "gün":
            dakika = value * 60 * 24 

        simdi = datetime.datetime.now()
        saat = simdi + datetime.timedelta(minutes=dakika)
        print(f"Hesaplananlanan zaman ➡️ İstenen Süre: {dakika} dakika, Hatırlatıcı Zamanı: {saat.strftime('%d.%m.%Y - %H:%M')}, Açıklama: {aciklama}")

        return {
            "zaman": saat,
            "aciklama": aciklama,
            "alarm_zamani_aktif": False,
            "alarm_zamani": None,
            "tekrar_tipi": None,
            "tekrar_gun": None,
            "tekrar_ay": None,
            "tekrarlama_araligi": None,
            "tarih": None
        }

    # 2. "her gün saat HH:MM ..."
    match2 = re.search(r"her (gün|hafta|ay) saat (\d{1,2}):(\d{2})(?:'da|'de|'te|'ta|’da|’de|’te|’ta)?\s*(.*)", text, re.IGNORECASE)
    if match2:
        print("✅ Match 2 found:")
        for i, a in enumerate(match2.groups()):
            print(f"   Group {i}: {a}")

        periyot = match2.group(1)
        periyot = 'her_' + periyot
        print(f"Periyot: {periyot}")

        hour = int(match2.group(2))
        minute = int(match2.group(3))
        aciklama = match2.group(4).strip() or "Doğal Komut"
        return {
            "zaman": 0,
            "aciklama": aciklama,
            "alarm_zamani_aktif": True,
            "alarm_zamani": f"{hour:02d}:{minute:02d}",
            "tekrar_tipi": periyot,
            "tekrar_gun": None,
            "tekrar_ay": None,
            "tekrarlama_araligi": 1,
            "tarih": None
        }

    # Dateparser ile tekrarlı olmayan hatırlatıcılar
    parsed_date = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})
    print("✅ Dateparser Match found:", parsed_date)
    if parsed_date:
        print("✅ Dateparser Match found:", parsed_date)

        tarih = parsed_date.date()
        saat = parsed_date.time()
        aciklama = text.strip() or "Doğal Komut"

        return {
            "zaman": parsed_date,
            "aciklama": aciklama,
            "alarm_zamani_aktif": True,
            "alarm_zamani": f"{saat.hour:02d}:{saat.minute:02d}" if saat else None,
            "tekrar_tipi": None,
            "tekrar_gun": None,
            "tekrar_ay": None,
            "tekrarlama_araligi": None,
            "tarih": parsed_date
        }

    # Dateparser-1 "her X günde bir saat HH:MM ..."
    match = re.search(r"her (\d+) günde bir saat (\d{1,2}):(\d{2})(?:'da|'de|'te|'ta|’da|’de|’te|’ta)?\s*(.*)", text, re.IGNORECASE)
    if match:
        print("✅ Dateparsder Match-1 found:", match.groups())

        tekrar_araligi_gun = int(match.group(1))
        hour = int(match.group(2))
        minute = int(match.group(3))
        aciklama = match.group(4).strip() or "Doğal Komut"

        simdi = datetime.datetime.now()
        baslangic_tarihi = simdi.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return {
            "zaman": baslangic_tarihi,
            "aciklama": aciklama,
            "alarm_zamani_aktif": True,
            "alarm_zamani": f"{hour:02d}:{minute:02d}",
            "tekrar_tipi": "her_gun",
            "tekrar_gun": None,
            "tekrar_ay": None,
            "tekrarlama_araligi": tekrar_araligi_gun,  
            "tarih": baslangic_tarihi
        }

    # 3. "yarın saat HH:MM ..."
    match3 = re.search(r"yar[ıi]n saat (\d{1,2}):(\d{2})(?:'da|'de|'te|'ta|’da|’de|’te|’ta)?\s*(.*)", text, re.IGNORECASE)
    if match3:
        print("✅ Match 3 found:", match3.groups())

        hour = int(match3.group(1))
        minute = int(match3.group(2))
        aciklama = match3.group(3).strip() or "Doğal Komut"
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        tarih = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return {
            "zaman": 0,
            "aciklama": aciklama,
            "alarm_zamani_aktif": True,
            "alarm_zamani": f"{hour:02d}:{minute:02d}",
            "tekrar_tipi": None,
            "tekrar_gun": None,
            "tekrar_ay": None,
            "tekrarlama_araligi": None,
            "tarih": tarih
        }

    # 4. "her cuma saat HH:MM ..."
    match4 = re.search(r"her (pazartesi|salı|sali|çarşamba|carsamba|perşembe|persembe|cuma|cumartesi|pazar) saat (\d{1,2}):(\d{2})(?:'da|'de|'te|'ta|’da|’de|’te|’ta)?\s*(.*)", text, re.IGNORECASE)
    if match4:
        print("✅ Match 4 found:", match4.groups())

        gun = match4.group(1).lower()
        hour = int(match4.group(2))
        minute = int(match4.group(3))
        aciklama = match4.group(4).strip() or "Doğal Komut"
        gun_map = {
            "pazartesi": 0, "salı": 1, "sali": 1, "çarşamba": 2, "carsamba": 2,
            "perşembe": 3, "persembe": 3, "cuma": 4, "cumartesi": 5, "pazar": 6
        }
        tekrar_gun = gun_map.get(gun, None)
        return {
            "zaman": 0,
            "aciklama": aciklama,
            "alarm_zamani_aktif": True,
            "alarm_zamani": f"{hour:02d}:{minute:02d}",
            "tekrar_tipi": "her_hafta",
            "tekrar_gun": tekrar_gun,
            "tekrar_ay": None,
            "tekrarlama_araligi": None,
            "tarih": None
        }

    # 5. "20 Temmuz 2025 saat 14:00 ..."
    match5 = re.search(r"(\d{1,2})\s*(ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)\s*(\d{4}) saat (\d{1,2}):(\d{2})(?:'da|'de|'te|'ta|’da|’de|’te|’ta)?\s*(.*)", text, re.IGNORECASE)
    if match5:
        print("✅ Match 5 found:", match5.groups())

        gun = int(match5.group(1))
        ay_str = match5.group(2).lower()
        yil = int(match5.group(3))
        hour = int(match5.group(4))
        minute = int(match5.group(5))
        aciklama = match5.group(6).strip() or "Doğal Komut"
        ay_map = {
            "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5,
            "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9,
            "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12
        }
        ay = ay_map.get(ay_str, None)
        if ay:
            tarih = datetime.datetime(yil, ay, gun, hour, minute)
            return {
                "zaman": 0,
                "aciklama": aciklama,
                "alarm_zamani_aktif": True,
                "alarm_zamani": f"{hour:02d}:{minute:02d}",
                "tekrar_tipi": None,
                "tekrar_gun": None,
                "tekrar_ay": None,
                "tekrarlama_araligi": None,
                "tarih": tarih
            }

    # 6. "X dakikada bir ..." veya "X saatte bir ..."
    match6 = re.search(r"(\d+)\s*(dakika|saat|saniye)da bir\s*(.*)", text, re.IGNORECASE)
    if match6:
        print("✅ Match 6 found:", match6.groups())

        value = int(match6.group(1))
        unit = match6.group(2).lower()
        aciklama = match6.group(3).strip() or "Doğal Komut"
        if unit == "dakika":
            tekrar_aralik_dakika = value
        elif unit == "saat":
            tekrar_aralik_dakika = value * 60
        elif unit == "saniye":
            tekrar_aralik_dakika = max(1, value // 60)
        return {
            "zaman": tekrar_aralik_dakika,
            "aciklama": aciklama,
            "alarm_zamani_aktif": False,
            "alarm_zamani": None,
            "tekrar_tipi": "aralikli",
            "tekrar_gun": None,
            "tekrar_ay": None,
            "tekrarlama_araligi": tekrar_aralik_dakika,
            "tarih": None
        }

    # 7. "her hafta cuma günü saat HH:MM ..."
    match7 = re.search(r"her hafta (pazartesi|salı|sali|çarşamba|carsamba|perşembe|persembe|cuma|cumartesi|pazar) günü saat (\d{1,2}):(\d{2})(?:'da|'de|'te|'ta|’da|’de|’te|’ta)?\s*(\d+)?\s*(dakika|saat)?\s*(.*)", text, re.IGNORECASE)
    if match7:
        print("✅ Match 7 found:", match7.groups())

        gun = match7.group(1).lower()
        hour = int(match7.group(2))
        minute = int(match7.group(3))
        sure_deger = match7.group(4)
        sure_birim = match7.group(5)
        aciklama = match7.group(6).strip() or "Doğal Komut"
        gun_map = {
            "pazartesi": 0, "salı": 1, "sali": 1, "çarşamba": 2, "carsamba": 2,
            "perşembe": 3, "persembe": 3, "cuma": 4, "cumartesi": 5, "pazar": 6
        }
        tekrar_gun = gun_map.get(gun, None)
        dakika = 0
        if sure_deger and sure_birim:
            val = int(sure_deger)
            if sure_birim == "dakika":
                dakika = val
            elif sure_birim == "saat":
                dakika = val * 60
        return {
            "zaman": dakika,
            "aciklama": aciklama,
            "alarm_zamani_aktif": True,
            "alarm_zamani": f"{hour:02d}:{minute:02d}",
            "tekrar_tipi": "her_hafta",
            "tekrar_gun": tekrar_gun,
            "tekrar_ay": None,
            "tekrarlama_araligi": None,
            "tarih": None
        }

    # 8. "her ayın X’inde saat HH:MM ..."
    match8 = re.search(r"her ay[ıi]n (\d{1,2})[’']?inde saat (\d{1,2}):(\d{2})(?:'da|'de|'te|'ta|’da|’de|’te|’ta)?\s*(.*)", text, re.IGNORECASE)
    if match8:
        print("✅ Match 8 found:", match8.groups())

        gun = int(match8.group(1))
        hour = int(match8.group(2))
        minute = int(match8.group(3))
        aciklama = match8.group(4).strip() or "Doğal Komut"
        return {
            "zaman": 0,
            "aciklama": aciklama,
            "alarm_zamani_aktif": True,
            "alarm_zamani": f"{hour:02d}:{minute:02d}",
            "tekrar_tipi": "her_ay",
            "tekrar_gun": gun,
            "tekrar_ay": None,
            "tekrarlama_araligi": None,
            "tarih": None
        }

    print("❌ Doğal Dil İşleme: Hiçbir eşleşme bulunamadı.")
    return None

