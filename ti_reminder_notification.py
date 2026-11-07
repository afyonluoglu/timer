# ti_reminder_notification.py
import os
import datetime
from timer_logger import record_log
from timer_reminder_system import HatirlaticiBildirimDialog
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent


def hatirlatici_bildirim_goster(manager, hatirlatici):
    """Hatırlatıcı bildirimini göster"""
    # Eğer hatırlatıcı zaten bir otomatik güncelleme işlemi geçirdiyse, tekrar bildirim gösterme
    if hasattr(hatirlatici, '_otomatik_guncellendi') and hasattr(hatirlatici, '_bildirim_gosterildi'):
        return
    manager.hatirlatici_ses_cal("ding-01.mp3")
    record_log(f"🎵 Hatırlatıcı {hatirlatici.not_metni} sesi çalınıdı...")

    # Bildirimi göstermeden önce mevcut zaman bilgisini kaydet
    gosterim_zamani = datetime.datetime.now()

    dialog = HatirlaticiBildirimDialog(manager.uygulama, hatirlatici)
    result = dialog.exec_()  # open() yerine exec_() kullanıyoruz

    if result == 2:
        record_log(f"🎉 Hatırlatıcı '{hatirlatici.not_metni}' tamamlandı")
    if result == 3:
        record_log(f"🎈 Hatırlatıcı'{hatirlatici.not_metni}', bu kez yapılmayacak")

    # Dialog kapandıktan sonra geçen süreyi hesapla
    gecen_sure = datetime.datetime.now() - gosterim_zamani
    gecen_saniye = gecen_sure.total_seconds()
    
    # Tüm aktif zamanlayıcıları güncelle
    for zamanlayici in manager.uygulama.aktif_zamanlayicilar:
        if zamanlayici.calisma_durumu:
            zamanlayici.sure -= int(gecen_saniye)  # Geçen süreyi çıkar        
    
    if result == 2 or result == 3:  # "Yapıldı" veya "yapılmayacak" butonuna basıldı
        if result == 2:
            record_log(f"✅ Hatırlatıcı'{hatirlatici.not_metni}', uyarı penceresinde  'yapıldı' olarak seçildi")
        if hatirlatici.tekrarlama_tipi != "yok":
            # Tekrarlayıcı için: sonraki tekrarı oluştur ve mevcut hatırlatıcıyı güncelle
            sonraki_tarih = hatirlatici.get_sonraki_tekrar_tarihi()
            if sonraki_tarih:
                # Mevcut hatırlatıcının son tekrar tarihini kaydet
                hatirlatici.son_tekrar_tarihi = hatirlatici.tarih
                
                # Mevcut hatırlatıcıyı sonraki tekrar tarihine güncelle
                hatirlatici.tarih = sonraki_tarih
                hatirlatici.yapildi = False  # Yeni tekrar için yapılmadı olarak işaretle
                
                # Otomatik güncelleme işaretini ekle
                hatirlatici._otomatik_guncellendi = True

                # Erteleme durumunu temizle
                hatirlatici.ertelendi = False
                # BİLDİRİM BAYRAĞI BURADA DA TUTULMALI!
                hatirlatici._bildirim_gosterildi = True           

                record_log(f"⏹️ Tekrarlı hatırlatıcı '{hatirlatici.not_metni}' sonraki tekrara güncellendi: {sonraki_tarih}")
            else:
                # Sonraki tekrar hesaplanamazsa normal şekilde yapıldı işaretle
                hatirlatici.yapildi = True
        else:
            record_log(f"✅ Normal hatırlatıcı '{hatirlatici.not_metni}' yapıldı olarak işaretlendi")
            # Normal hatırlatıcı için sadece yapıldı işaretle
            hatirlatici.yapildi = True
        
        # Bildirim flag'ini temizle
        if hasattr(hatirlatici, '_bildirim_gosterildi'):
            delattr(hatirlatici, '_bildirim_gosterildi')

        # Erteleme flag'ini de temizle (eğer varsa)
        if hasattr(hatirlatici, '_ertelendi'):
            delattr(hatirlatici, '_ertelendi')

        manager.hatirlatici_listelerini_guncelle()
        manager.uygulama.ayarlari_kaydet()
    else:
        record_log(f"⏱️ Hatırlatıcı '{hatirlatici.not_metni}' için 'Daha Sonra' seçildi")
        # "Daha Sonra" seçildiğinde erteleme flag'i ekle
        hatirlatici.ertelendi = True
        hatirlatici._ertelendi = True

        # Bildirim flag'ini temizle ki tekrar bildirim gelsin
        if hasattr(hatirlatici, '_bildirim_gosterildi'):
            delattr(hatirlatici, '_bildirim_gosterildi')
        
        manager.hatirlatici_listelerini_guncelle()
        manager.uygulama.ayarlari_kaydet()


def hatirlatici_ses_cal(manager, ses_dosyasi="ding-01.mp3"):
    """Hatırlatıcı için ses çal"""
    dosya_yolu = os.path.join(manager.uygulama.veri_klasoru, ses_dosyasi)
    
    # Dosya var mı kontrol et
    if not os.path.exists(dosya_yolu):
        dosya_yolu = os.path.join(manager.uygulama.veri_klasoru, ses_dosyasi)
        if not os.path.exists(dosya_yolu):
            record_log(f"❗ Hatırlatıcı ses dosyası bulunamadı: {ses_dosyasi}", "error")
            return
    
    try:
        url = QUrl.fromLocalFile(dosya_yolu)
        content = QMediaContent(url)
        manager.uygulama.medya_oynatici.setMedia(content)
        manager.uygulama.medya_oynatici.play()
    except Exception as e:
        record_log(f"❗ Hatırlatıcı sesi çalınırken hata: {str(e)}", "error")

