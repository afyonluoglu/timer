import os
import datetime
from PyQt5.QtWidgets import QDialog, QMessageBox, QMenu
from PyQt5.QtCore import QUrl, QTime
from PyQt5.QtMultimedia import QMediaContent
from timer_logger import record_log
from timer_reminder_system import HatirlaticiBildirimDialog, HatirlaticiDialog, Hatirlatici
from timer_helpers import show_toast
from timer_formatter import format_time

class HatirlaticiManager:
    """
    Hatırlatıcı sisteminin UI ve yönetim işlevlerini sağlayan yardımcı sınıf.
    Ana ZamanlayiciUygulamasi sınıfı ile birlikte çalışır.
    """
    
    def __init__(self, uygulama):
        """
        uygulama: ZamanlayiciUygulamasi örneği
        """
        self.uygulama = uygulama
        self._sorted_hatirlatici_ids = []
        
    def yeni_hatirlatici_ekle(self):
        """Yeni hatırlatıcı ekleme diyaloğunu aç"""
        dialog = HatirlaticiDialog(self.uygulama)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values['not_metni']:
                QMessageBox.warning(self.uygulama, "Uyarı", "Hatırlatma metni boş olamaz!")
                return

            self.uygulama.hatirlatici_id_sayaci += 1
            yeni_hatirlatici = Hatirlatici(
                id=self.uygulama.hatirlatici_id_sayaci,
                tarih=values['tarih'],
                saat=values['saat'],
                not_metni=values['not_metni'],
                tekrarlama_tipi=values['tekrarlama_tipi'],
                tekrarlama_araligi=values['tekrarlama_araligi'],
                hafta_gunu=values['hafta_gunu']  # Yeni parametre
            )
            
            self.uygulama.hatirlaticilar.append(yeni_hatirlatici)
            self.hatirlatici_listelerini_guncelle()
            self.uygulama.ayarlari_kaydet()

    def hatirlatici_sag_tik_menu(self, position):
        """Tüm hatırlatıcılar listesi için sağ tık menüsü"""
        item = self.uygulama.tum_hatirlaticilar_list.itemAt(position)
        if item:
            menu = QMenu(self.uygulama)
            tamamlandi_action = menu.addAction("Tamamlandı")
            duzenle_action = menu.addAction("Düzenle")
            sil_action = menu.addAction("Sil")
            action = menu.exec_(self.uygulama.tum_hatirlaticilar_list.mapToGlobal(position))

            if action == tamamlandi_action:
                # Mark selected reminder as completed and handle repeats
                hatirlatici = self.get_hatirlatici_from_sorted_list(self.uygulama.tum_hatirlaticilar_list.row(item))
                if hatirlatici:
                    # --- EKLENDİ: Kaç dakika önce tamamlandı hesaplama ---
                    simdi = datetime.datetime.now()
                    hatirlatici_zamani = hatirlatici.get_datetime()
                    fark = hatirlatici_zamani - simdi
                    dakika_farki = int(fark.total_seconds() // 60)
                    erken = f"{dakika_farki} dakika önce"
                    if dakika_farki > 60:
                        # print(f"Hatırlatıcı ID {hatirlatici.id} için fark 60 dakikadan fazla: {dakika_farki} dakika")
                        # print(f"{dakika_farki*60}")
                        dakika_farki = format_time(dakika_farki*60)
                        erken = f"{dakika_farki} süre önce"

                    # Handle repeating reminders
                    if hatirlatici.tekrarlama_tipi != "yok":
                        sonraki = hatirlatici.get_sonraki_tekrar_tarihi()
                        if sonraki:
                            hatirlatici.son_tekrar_tarihi = hatirlatici.tarih
                            hatirlatici.tarih = sonraki
                            hatirlatici.yapildi = False
                            hatirlatici._otomatik_guncellendi = True
                            hatirlatici.ertelendi = False
                        else:
                            hatirlatici.yapildi = True
                    else:
                        hatirlatici.yapildi = True
                        # Tekrarlamayan hatırlatıcıyı listeden kaldır - Mustafa 03.09.2025
                        if hatirlatici in self.uygulama.hatirlaticilar:
                            self.uygulama.hatirlaticilar.remove(hatirlatici)
                            print(f"🚩 Tekrarlamayan hatırlatıcı  '{hatirlatici.not_metni}' listeden kaldırıldı (tamamlandı olarak işaretlendi)")


                    # Clear any notification or snooze flags
                    if hasattr(hatirlatici, '_bildirim_gosterildi'):
                        delattr(hatirlatici, '_bildirim_gosterildi')
                    if hasattr(hatirlatici, '_ertelendi'):
                        delattr(hatirlatici, '_ertelendi')
                    # Refresh lists and save settings
                    self.hatirlatici_listelerini_guncelle()
                    self.uygulama.ayarlari_kaydet()
                    record_log(f"🔔 Hatırlatıcı '{hatirlatici.not_metni}', {erken}, 'tamamlandı' olarak işaretlendi")                    
            elif action == duzenle_action:
                # Sıralı listeden gerçek hatırlatıcıyı bul
                hatirlatici = self.get_hatirlatici_from_sorted_list(self.uygulama.tum_hatirlaticilar_list.row(item))
                if hatirlatici:
                    self.hatirlatici_duzenle_by_object(hatirlatici)                    

            elif action == sil_action:
                # Sıralı listeden gerçek hatırlatıcıyı bul
                hatirlatici = self.get_hatirlatici_from_sorted_list(self.uygulama.tum_hatirlaticilar_list.row(item))
                if hatirlatici:
                    self.hatirlatici_sil_by_object(hatirlatici)


    def get_hatirlatici_from_sorted_list(self, sorted_index):
        """Sıralı listeden gerçek hatırlatıcı objesini döndür - ID tabanlı"""
        try:
            if hasattr(self.uygulama, '_sorted_hatirlatici_ids') and 0 <= sorted_index < len(self.uygulama._sorted_hatirlatici_ids):
                hatirlatici_id = self.uygulama._sorted_hatirlatici_ids[sorted_index]
                
                # ID'ye göre hatırlatıcıyı bul
                for hatirlatici in self.uygulama.hatirlaticilar:
                    if hatirlatici.id == hatirlatici_id:
                        return hatirlatici
                        
        except Exception as e:
            record_log(f"Hatırlatıcı bulma hatası: {e}", "error")
        return None

    def hatirlatici_duzenle_by_object(self, hatirlatici):
        from timer_reminder_system import HatirlaticiDialog
        """Hatırlatıcı objesini kullanarak düzenleme"""
        dialog = HatirlaticiDialog(self.uygulama, hatirlatici)
        
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values['not_metni']:
                QMessageBox.warning(self.uygulama, "Uyarı", "Hatırlatma metni boş olamaz!")
                return
            
            # Eski ve yeni tarihleri karşılaştır
            eski_tarih = hatirlatici.tarih
            eski_saat = hatirlatici.saat
            yeni_tarih = values['tarih']
            yeni_saat = values['saat']
            
            # Hatırlatıcı bilgilerini güncelle
            hatirlatici.tarih = yeni_tarih
            hatirlatici.saat = yeni_saat
            hatirlatici.not_metni = values['not_metni']
            hatirlatici.tekrarlama_tipi = values['tekrarlama_tipi']
            hatirlatici.tekrarlama_araligi = values['tekrarlama_araligi']
            hatirlatici.hafta_gunu = values['hafta_gunu']
            
            # Eğer tarih/saat değiştiyse ve gelecek bir zamana ayarlandıysa yapıldı durumunu sıfırla
            yeni_datetime = hatirlatici.get_datetime()
            if (eski_tarih != yeni_tarih or eski_saat.toString('HH:mm') != yeni_saat.toString('HH:mm')):
                # Bildirim flag'ini temizle
                if hasattr(hatirlatici, '_bildirim_gosterildi'):
                    delattr(hatirlatici, '_bildirim_gosterildi')
                    # print(f"Hatırlatıcı ID {hatirlatici.id}: Bildirim flag'i temizlendi (zaman değiştirildi)")
                
                # Otomatik güncelleme flag'ini temizle
                if hasattr(hatirlatici, '_otomatik_guncellendi'):
                    delattr(hatirlatici, '_otomatik_guncellendi')
                    # print(f"Hatırlatıcı ID {hatirlatici.id}: Otomatik güncelleme flag'i temizlendi (zaman değiştirildi)")
                
                # Eğer yeni tarih/saat gelecekteyse, yapıldı durumunu sıfırla
                if yeni_datetime > datetime.datetime.now():
                    was_completed = hatirlatici.yapildi
                    hatirlatici.yapildi = False
                    hatirlatici.ertelendi = False
                    
                    # if was_completed:
                        # print(f"Hatırlatıcı ID {hatirlatici.id}: Yapıldı durumu sıfırlandı (gelecek zamana ayarlandı)")
            
            record_log(f"✏️  Hatırlatıcı '{hatirlatici.not_metni}' (ID {hatirlatici.id}) düzenlendi: {eski_tarih.strftime('%d.%m.%Y')} - {eski_saat.toString('HH:mm')} -> {yeni_tarih.strftime('%d.%m.%Y')} - {yeni_saat.toString('HH:mm')}")

            self.hatirlatici_listelerini_guncelle()
            self.uygulama.ayarlari_kaydet()

    def hatirlatici_sil_by_object(self, hatirlatici):
        """Hatırlatıcı objesini kullanarak silme"""
        # Hatırlatıcı bilgilerini onay mesajında göster
        tarih_str = hatirlatici.tarih.strftime('%d.%m.%Y')
        saat_str = hatirlatici.saat.toString('HH:mm')
        
        # Tekrarlama bilgisini ekle
        tekrar_bilgisi = ""
        if hatirlatici.tekrarlama_tipi != "yok":
            if hatirlatici.tekrarlama_tipi == "gun":
                if hatirlatici.tekrarlama_araligi == 1:
                    tekrar_bilgisi = "\nTekrarlama: Her gün"
                else:
                    tekrar_bilgisi = f"\nTekrarlama: Her {hatirlatici.tekrarlama_araligi} günde bir"
            elif hatirlatici.tekrarlama_tipi == "hafta":
                gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
                gun_ismi = gun_isimleri[hatirlatici.hafta_gunu] if hatirlatici.hafta_gunu is not None else "Bilinmeyen"
                tekrar_bilgisi = f"\nTekrarlama: Her {hatirlatici.tekrarlama_araligi} haftada bir, {gun_ismi}"
            elif hatirlatici.tekrarlama_tipi == "ay":
                if hatirlatici.tekrarlama_araligi == 1:
                    tekrar_bilgisi = "\nTekrarlama: Her gün"
                else:                
                    tekrar_bilgisi = f"\nTekrarlama: Her {hatirlatici.tekrarlama_araligi} ayda bir"
        
        # Hatırlatıcı metnini kısalt (çok uzunsa)
        max_metin_uzunlugu = 50
        hatirlatici_metni = hatirlatici.not_metni
        if len(hatirlatici_metni) > max_metin_uzunlugu:
            hatirlatici_metni = hatirlatici_metni[:max_metin_uzunlugu] + "..."
        
        # Detaylı onay mesajı oluştur
        onay_mesaji = f"""Bu hatırlatıcıyı silmek istediğinizden emin misiniz?

    📅 Tarih: {tarih_str}
    ⏰ Saat: {saat_str}
    📝 Metin: {hatirlatici_metni}{tekrar_bilgisi}

    Bu işlem geri alınamaz!"""
        
        reply = QMessageBox.question(
            self.uygulama, 
            "Hatırlatıcı Sil", 
            onay_mesaji,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Varsayılan olarak "Hayır" seçili
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.uygulama.hatirlaticilar.remove(hatirlatici)
                self.hatirlatici_listelerini_guncelle()
                self.uygulama.ayarlari_kaydet()
                
                record_log(f"🗑️ Hatırlatıcı '{hatirlatici_metni[:30]}' silindi")                
                # Başarılı silme mesajı 
                QMessageBox.information(
                    self.uygulama, 
                    "Başarılı", 
                    f"Hatırlatıcı başarıyla silindi:\n{tarih_str} {saat_str} - {hatirlatici_metni[:30]}..."
                )
            except ValueError:
                QMessageBox.warning(self.uygulama, "Hata", "Hatırlatıcı listede bulunamadı!")
                
    def gecmis_hatirlatici_sag_tik_menu(self, position):
        """Geçmiş hatırlatıcılar listesi için sağ tık menüsü"""
        item = self.uygulama.gecmis_hatirlaticilar_list.itemAt(position)
        if item:
            menu = QMenu(self.uygulama)
            yapildi_action = menu.addAction("Yapıldı")
            action = menu.exec_(self.uygulama.gecmis_hatirlaticilar_list.mapToGlobal(position))
            
            if action == yapildi_action:
                # Geçmiş listesindeki hatırlatıcıyı bul
                hatirlatici = self.get_hatirlatici_from_gecmis_list(self.uygulama.gecmis_hatirlaticilar_list.row(item))
                record_log(f"✅ Hatırlatıcı'{hatirlatici.not_metni}', 'YAPILMAMIŞLAR'  listesinde  'yapıldı' olarak işaretlendi")

                if hatirlatici:
                    # Tekrarlı hatırlatıcı kontrolü ekle
                    if hatirlatici.tekrarlama_tipi != "yok":
                        # Bir sonraki tekrarı hesapla
                        sonraki_tarih = hatirlatici.get_sonraki_tekrar_tarihi()
                        if sonraki_tarih:
                            # Mevcut hatırlatıcının son tekrar tarihini kaydet
                            hatirlatici.son_tekrar_tarihi = hatirlatici.tarih
                            
                            # Hatırlatıcıyı sonraki tekrar tarihine güncelle
                            hatirlatici.tarih = sonraki_tarih
                            hatirlatici.yapildi = False  # Yeni tekrar için yapılmadı olarak işaretle
                            
                            # Otomatik güncelleme işaretini ekle
                            hatirlatici._otomatik_guncellendi = True

                            # Erteleme durumunu temizle
                            hatirlatici.ertelendi = False
                            
                            record_log(f"⏹️ Tekrarlı hatırlatıcı '{hatirlatici.not_metni}' sonraki tekrara güncellendi: {sonraki_tarih}")
                        else:
                            # Sonraki tekrar hesaplanamazsa normal şekilde yapıldı işaretle
                            hatirlatici.yapildi = True
                    else:
                        # Normal hatırlatıcı için sadece yapıldı işaretle
                        hatirlatici.yapildi = True
                    
                    # Bildirim ve erteleme flag'lerini temizle
                    if hasattr(hatirlatici, '_bildirim_gosterildi'):
                        delattr(hatirlatici, '_bildirim_gosterildi')
                    if hasattr(hatirlatici, '_ertelendi'):
                        delattr(hatirlatici, '_ertelendi')

                    self.hatirlatici_listelerini_guncelle()
                    self.uygulama.ayarlari_kaydet()

    def get_hatirlatici_from_gecmis_list(self, gecmis_index):
        """Geçmiş listesinden gerçek hatırlatıcı objesini döndür"""
        try:
            gecmis_hatirlaticilar = [h for h in self.uygulama.hatirlaticilar if h.is_gecmis() and not h.yapildi]
            gecmis_hatirlaticilar.sort(key=lambda h: h.get_datetime(), reverse=True)
            
            if 0 <= gecmis_index < len(gecmis_hatirlaticilar):
                return gecmis_hatirlaticilar[gecmis_index]
        except Exception as e:
            record_log(f"Geçmiş hatırlatıcı bulma hatası: {e}", "error")
        return None

    def hatirlatici_yapildi_isaretle(self, item):
        """Hatırlatıcıyı yapıldı olarak işaretle"""
        # Geçmiş listesindeki index'i bul
        gecmis_index = self.uygulama.gecmis_hatirlaticilar_list.row(item)
        gecmis_hatirlaticilar = [h for h in self.uygulama.hatirlaticilar if h.is_gecmis() and not h.yapildi]
        
        if 0 <= gecmis_index < len(gecmis_hatirlaticilar):
            hatirlatici = gecmis_hatirlaticilar[gecmis_index]
            
            # Tekrarlı hatırlatıcı kontrolü ekle
            if hatirlatici.tekrarlama_tipi != "yok":
                # Bir sonraki tekrarı hesapla
                sonraki_tarih = hatirlatici.get_sonraki_tekrar_tarihi()
                if sonraki_tarih:
                    # Mevcut hatırlatıcının son tekrar tarihini kaydet
                    hatirlatici.son_tekrar_tarihi = hatirlatici.tarih
                    
                    # Hatırlatıcıyı sonraki tekrar tarihine güncelle
                    hatirlatici.tarih = sonraki_tarih
                    hatirlatici.yapildi = False  # Yeni tekrar için yapılmadı olarak işaretle
                    
                    # Otomatik güncelleme işaretini ekle
                    hatirlatici._otomatik_guncellendi = True
                    
                    # Erteleme durumunu temizle
                    hatirlatici.ertelendi = False
                    
                    record_log(f"✅ Tekrarlı hatırlatıcı ID {hatirlatici.id} sonraki tekrara güncellendi: {sonraki_tarih}")
                else:
                    # Sonraki tekrar hesaplanamazsa normal şekilde yapıldı işaretle
                    hatirlatici.yapildi = True
            else:
                # Normal hatırlatıcı için sadece yapıldı işaretle
                hatirlatici.yapildi = True
            
            # Bildirim ve erteleme flag'lerini temizle
            if hasattr(hatirlatici, '_bildirim_gosterildi'):
                delattr(hatirlatici, '_bildirim_gosterildi')
            if hasattr(hatirlatici, '_ertelendi'):
                delattr(hatirlatici, '_ertelendi')
            
            self.hatirlatici_listelerini_guncelle()
            self.uygulama.ayarlari_kaydet()

    def hatirlatici_listelerini_guncelle(self, kalan_sure_guncelle=False):
        """Hatırlatıcı listelerini güncelle"""
        # Eğer sadece kalan süreyi güncellemek istiyorsak, tam yenileme yapmak yerine
        # sadece görünen metinleri güncelleyelim
        if kalan_sure_guncelle and self.uygulama.tum_hatirlaticilar_list.count() > 0:
            simdi = datetime.datetime.now()
            for i in range(self.uygulama.tum_hatirlaticilar_list.count()):
                item = self.uygulama.tum_hatirlaticilar_list.item(i)
                if i < len(self.uygulama._sorted_hatirlatici_ids):
                    hatirlatici_id = self.uygulama._sorted_hatirlatici_ids[i]
                    hatirlatici = next((h for h in self.uygulama.hatirlaticilar if h.id == hatirlatici_id), None)
                    if hatirlatici and not hatirlatici.yapildi and not hatirlatici.is_gecmis():
                        # Sadece aktif hatırlatıcılar için kalan süreyi güncelle
                        kalan_sure = hatirlatici.get_datetime() - simdi
                        kalan_str = self.kalan_sure_metni_olustur(kalan_sure)

                        # Mevcut metni al, kalan süre kısmını güncelle
                        mevcut_metin = item.text()
                        if "[" in mevcut_metin and "]" in mevcut_metin:
                            yeni_metin = mevcut_metin.split("[")[0] + kalan_str
                            item.setText(yeni_metin)
            return


        # Önce tekrarlı hatırlatıcıları otomatik güncelle
        self.tekrarli_hatirlaticilari_guncelle()
        
        # Tüm hatırlatıcılar listesi - tarih sırasına göre (yakın olanlar en üstte)
        self.uygulama.tum_hatirlaticilar_list.clear()
        
        # Hatırlatıcıları duruma göre ayır
        aktif_hatirlaticilar = []  # Süresi dolmamış VE yapılmamış
        gecmis_hatirlaticilar = []  # Süresi dolmuş VEYA yapılmış

        simdi = datetime.datetime.now()  # Mevcut zamanı al
        
        for hatirlatici in self.uygulama.hatirlaticilar:
            # Düzenleme sonrasında otomatik güncelleme flag'ini temizle
            if hasattr(hatirlatici, '_otomatik_guncellendi'):
                # Eğer hatırlatıcı artık gelecekteyse flag'i temizle
                if not hatirlatici.is_gecmis():
                    delattr(hatirlatici, '_otomatik_guncellendi')
            
            # Bildirim flag'ini de kontrol et - eğer hatırlatıcı düzenlenip gelecekte bir zamana ayarlanmışsa temizle
            if hasattr(hatirlatici, '_bildirim_gosterildi') and not hatirlatici.is_gecmis():
                delattr(hatirlatici, '_bildirim_gosterildi')
            
            # Hatırlatıcının durumunu kontrol et
            if hatirlatici.yapildi:
                gecmis_hatirlaticilar.append(hatirlatici)
            # Ertelenmiş hatırlatıcılar aktif olarak işaretlensin
            elif hasattr(hatirlatici, '_ertelendi') or getattr(hatirlatici, 'ertelendi', False):
                aktif_hatirlaticilar.append(hatirlatici)
            elif hatirlatici.is_gecmis():
                gecmis_hatirlaticilar.append(hatirlatici)
            else:
                aktif_hatirlaticilar.append(hatirlatici)

        # Aktif hatırlatıcıları tarihe göre sırala (en yakın en üstte)
        aktif_hatirlaticilar.sort(key=lambda h: h.get_datetime())
        # Geçmiş hatırlatıcıları tarihe göre sırala (en yeni en üstte)
        gecmis_hatirlaticilar.sort(key=lambda h: h.get_datetime(), reverse=True)
        
        # ID'li liste oluştur (sıralama referansı için)
        self.uygulama._sorted_hatirlatici_ids = []

        # Önce aktif hatırlatıcıları ekle
        for hatirlatici in aktif_hatirlaticilar:
            self.uygulama._sorted_hatirlatici_ids.append(hatirlatici.id)

            tekrar_bilgisi = ""
            if hatirlatici.tekrarlama_tipi != "yok":
                if hatirlatici.tekrarlama_tipi == "gun":
                    if hatirlatici.tekrarlama_araligi == 1:
                        tekrar_bilgisi = " (✨Her gün)"
                    else:
                        tekrar_bilgisi = f" (⏹️Her {hatirlatici.tekrarlama_araligi} günde bir)"
                elif hatirlatici.tekrarlama_tipi == "hafta":
                    gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
                    gun_ismi = gun_isimleri[hatirlatici.hafta_gunu] if hatirlatici.hafta_gunu is not None else "Bilinmeyen"
                    if hatirlatici.tekrarlama_araligi == 1:
                        tekrar_bilgisi = f" (🚩Her hafta, {gun_ismi})"
                    else:
                        tekrar_bilgisi = f" (♦️Her {hatirlatici.tekrarlama_araligi} haftada bir, {gun_ismi})"
                elif hatirlatici.tekrarlama_tipi == "ay":
                    if hatirlatici.tekrarlama_araligi == 1:
                        tekrar_bilgisi = " (📆Her ay)"
                    else:
                        tekrar_bilgisi = f" (🌮Her {hatirlatici.tekrarlama_araligi} ayda bir)"
            
            # Kalan süreyi hesapla
            hatirlatici_zamani = hatirlatici.get_datetime()
            kalan_sure = hatirlatici_zamani - simdi
            
            if kalan_sure.days > 0:
                # saat = int(kalan_sure.total_seconds() // 3600)
                saat = int((kalan_sure.total_seconds() % 86400) // 3600)  # 1 gün = 86400 sn
                kalan_str = f" [{kalan_sure.days} gün {saat} saat kaldı]"
            elif kalan_sure.total_seconds() > 3600:  # 1 saatten fazla
                saat = int(kalan_sure.total_seconds() // 3600)
                dakika = int((kalan_sure.total_seconds() % 3600) // 60)
                kalan_str = f" [{saat}s {dakika}dk kaldı]"
            elif kalan_sure.total_seconds() > 60:  # 1 dakikadan fazla
                dakika = int(kalan_sure.total_seconds() // 60)
                kalan_str = f" [{dakika} dk kaldı]"
            else:
                kalan_str = " [Az kaldı!]"
            
            # Otomatik güncellenmiş tekrar ise bunu belirt 
            otomatik_guncelleme_str = ""
            if hasattr(hatirlatici, '_otomatik_guncellendi') and hatirlatici._otomatik_guncellendi:
                otomatik_guncelleme_str = " 🔄"
            
            item_text = f"🔔 {hatirlatici.tarih.strftime('%d.%m.%Y')} {hatirlatici.saat.toString('HH:mm')} - {hatirlatici.not_metni[:30]}...{tekrar_bilgisi}{otomatik_guncelleme_str}{kalan_str}"
            self.uygulama.tum_hatirlaticilar_list.addItem(item_text)

        # Sonra geçmiş hatırlatıcıları ekle
        for hatirlatici in gecmis_hatirlaticilar:
            self.uygulama._sorted_hatirlatici_ids.append(hatirlatici.id)

            durum = " ✓" if hatirlatici.yapildi else ""
            gecmis = " (Geçmiş)" if hatirlatici.is_gecmis() and not hatirlatici.yapildi else ""
            
            tekrar_bilgisi = ""
            if hatirlatici.tekrarlama_tipi != "yok":
                if hatirlatici.tekrarlama_tipi == "gun":
                    tekrar_bilgisi = f" (Her {hatirlatici.tekrarlama_araligi} günde bir)"
                elif hatirlatici.tekrarlama_tipi == "hafta":
                    gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
                    gun_ismi = gun_isimleri[hatirlatici.hafta_gunu] if hatirlatici.hafta_gunu is not None else "Bilinmeyen"
                    tekrar_bilgisi = f" (Her {hatirlatici.tekrarlama_araligi} haftada bir, {gun_ismi})"
                elif hatirlatici.tekrarlama_tipi == "ay":
                    tekrar_bilgisi = f" (Her {hatirlatici.tekrarlama_araligi} ayda bir)"
            
            item_text = f"⏰ {hatirlatici.tarih.strftime('%d.%m.%Y')} {hatirlatici.saat.toString('HH:mm')} - {hatirlatici.not_metni[:30]}...{tekrar_bilgisi}{durum}{gecmis}"
            self.uygulama.tum_hatirlaticilar_list.addItem(item_text)

        # Geçmiş/Yapılmamış hatırlatıcılar listesi
        self.uygulama.gecmis_hatirlaticilar_list.clear()

        # Tekrarlı olmayan ve geçmiş olan hatırlatıcıları + 
        # Tekrarlı olup bildirim gösterilmiş ama "Daha Sonra" denmiş olanları dahil et
        gecmis_hatirlaticilar_sadece = []

        for h in self.uygulama.hatirlaticilar:
            # Zamanı geçmiş ve henüz 'yapıldı' olarak işaretlenmemiş tüm hatırlatıcıları listeye ekle.
            # Bu, hem normal hem de tekrarlı hatırlatıcılar için geçerlidir.
            if not h.yapildi and h.is_gecmis():
                gecmis_hatirlaticilar_sadece.append(h)

        gecmis_hatirlaticilar_sadece.sort(key=lambda h: h.get_datetime(), reverse=True)
        
        for hatirlatici in gecmis_hatirlaticilar_sadece:
            tekrar_bilgisi = ""
            if hatirlatici.tekrarlama_tipi != "yok":
                if hatirlatici.tekrarlama_tipi == "gun":
                    tekrar_bilgisi = f" (Her {hatirlatici.tekrarlama_araligi} günde bir)"
                elif hatirlatici.tekrarlama_tipi == "hafta":
                    gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
                    gun_ismi = gun_isimleri[hatirlatici.hafta_gunu] if hatirlatici.hafta_gunu is not None else "Bilinmeyen"
                    tekrar_bilgisi = f" (Her {hatirlatici.tekrarlama_araligi} haftada bir, {gun_ismi})"
                elif hatirlatici.tekrarlama_tipi == "ay":
                    tekrar_bilgisi = f" (Her {hatirlatici.tekrarlama_araligi} ayda bir)"
            
            # "Daha Sonra" denmiş olanları belirt
            daha_sonra_str = ""
            if hasattr(hatirlatici, '_bildirim_gosterildi'):
                daha_sonra_str = " [Daha Sonra Denildi]"
            
            item_text = f"{hatirlatici.tarih.strftime('%d.%m.%Y')} {hatirlatici.saat.toString('HH:mm')} - {hatirlatici.not_metni[:30]}...{tekrar_bilgisi}{daha_sonra_str}"
            self.uygulama.gecmis_hatirlaticilar_list.addItem(item_text)

    def kalan_sure_metni_olustur(self, kalan_sure):
        """Kalan süreyi formatlı metin olarak döndürür"""
        if kalan_sure.days > 0:
            saat = int((kalan_sure.total_seconds() % 86400) // 3600)
            return f"[{kalan_sure.days} gün {saat} saat kaldı]"            
        elif kalan_sure.total_seconds() > 3600:  # 1 saatten fazla
            saat = int(kalan_sure.total_seconds() // 3600)
            dakika = int((kalan_sure.total_seconds() % 3600) // 60)
            return f"[{saat}s {dakika}dk kaldı]"
        elif kalan_sure.total_seconds() > 60:  # 1 dakikadan fazla
            dakika = int(kalan_sure.total_seconds() // 60)
            return f"[{dakika} dk kaldı]"
        else:
            return "[Az kaldı!]"

    def tekrarli_hatirlaticilari_guncelle(self):
        """Geçmiş olan tekrarlı hatırlatıcıları otomatik olarak sonraki tekrar tarihine güncelle"""
        guncelleme_yapildi = False
        
        for hatirlatici in self.uygulama.hatirlaticilar:
            # Sadece tekrarlı, yapılmamış ve geçmiş olan hatırlatıcıları kontrol et
            if (hatirlatici.tekrarlama_tipi != "yok" and 
                not hatirlatici.yapildi and 
                hatirlatici.is_gecmis() and
                not hasattr(hatirlatici, '_otomatik_guncellendi') and
                not hasattr(hatirlatici, '_ertelendi') and 
                not getattr(hatirlatici, 'ertelendi', False)):  # Yeni kontrol satırı
                
                # Sonraki tekrar tarihini hesapla
                sonraki_tarih = hatirlatici.get_sonraki_tekrar_tarihi()
                
                if sonraki_tarih:
                    # Hatırlatıcıyı sonraki tekrar tarihine güncelle
                    eski_tarih = hatirlatici.tarih
                    hatirlatici.son_tekrar_tarihi = hatirlatici.tarih  # Eski tarihi kaydet
                    hatirlatici.tarih = sonraki_tarih
                    hatirlatici._otomatik_guncellendi = True  # Otomatik güncellendiğini işaretle
                    
                    # Eski bildirim flag'lerini temizle
                    if hasattr(hatirlatici, '_bildirim_gosterildi'):
                        delattr(hatirlatici, '_bildirim_gosterildi')
                    toast_msg_time = eski_tarih.strftime('%d.%m.%Y') + ' ' + hatirlatici.saat.toString('HH:mm')
                    show_toast(self.uygulama, toast_msg_time, hatirlatici.not_metni, duration=0)
                    record_log(f"✨ Hatırlatıcı '{hatirlatici.not_metni}' (ID {hatirlatici.id}) otomatik güncellendi: {eski_tarih} -> {sonraki_tarih}")
                    guncelleme_yapildi = True
        
        # Eğer güncelleme yapıldıysa ayarları kaydet
        if guncelleme_yapildi:
            self.uygulama.ayarlari_kaydet()

    def hatirlatici_kontrol(self):
        """Zamanı gelen hatırlatıcıları kontrol et"""
        simdi = datetime.datetime.now()
        
        for hatirlatici in self.uygulama.hatirlaticilar[:]:  # Kopya üzerinde döngü
            if not hatirlatici.yapildi:
                hatirlatici_zamani = hatirlatici.get_datetime()
                
                # Otomatik güncellenen hatırlatıcıların hemen tekrar bildirimi göstermesini engelle
                if hasattr(hatirlatici, '_otomatik_guncellendi') and hasattr(hatirlatici, '_bildirim_gosterildi'):
                    if (simdi - hatirlatici.get_datetime()).total_seconds() < 60:  # 1 dakikadan az fark varsa
                        continue
    
                # Normal hatırlatıcı kontrolü (tekrarlı olanlar da dahil, artık otomatik güncellendikleri için)
                if hatirlatici_zamani <= simdi and not hasattr(hatirlatici, '_bildirim_gosterildi'):
                    self.hatirlatici_bildirim_goster(hatirlatici)
                    hatirlatici._bildirim_gosterildi = True
                    
                    # Otomatik güncelleme işaretini kaldır
                    # if hasattr(hatirlatici, '_otomatik_guncellendi'):
                    #     delattr(hatirlatici, '_otomatik_guncellendi')
                    
                    # print("liste normal güncelleniyor")
                    self.hatirlatici_listelerini_guncelle()

    def hatirlatici_bildirim_goster(self, hatirlatici):
        """Hatırlatıcı bildirimini göster"""
        # Eğer hatırlatıcı zaten bir otomatik güncelleme işlemi geçirdiyse, tekrar bildirim gösterme
        if hasattr(hatirlatici, '_otomatik_guncellendi') and hasattr(hatirlatici, '_bildirim_gosterildi'):
            return
        self.hatirlatici_ses_cal("ding-01.mp3")
        record_log(f"🎵 Hatırlatıcı {hatirlatici.not_metni} sesi çalınıdı...")


        # Bildirimi göstermeden önce mevcut zaman bilgisini kaydet
        gosterim_zamani = datetime.datetime.now()

        dialog = HatirlaticiBildirimDialog(self.uygulama, hatirlatici)
        result = dialog.exec_()  # open() yerine exec_() kullanıyoruz

        if result == 2:
            record_log(f"🎉 Hatırlatıcı '{hatirlatici.not_metni}' tamamlandı")
        if result == 3:
            record_log(f"🎈 Hatırlatıcı'{hatirlatici.not_metni}', bu kez yapılmayacak")

        # Dialog kapandıktan sonra geçen süreyi hesapla
        gecen_sure = datetime.datetime.now() - gosterim_zamani
        gecen_saniye = gecen_sure.total_seconds()
        
        # Tüm aktif zamanlayıcıları güncelle
        for zamanlayici in self.uygulama.aktif_zamanlayicilar:
            if zamanlayici.calisma_durumu:
                zamanlayici.sure -= int(gecen_saniye)  # Geçen süreyi çıkar        
        
        if result == 2 or  result == 3:  # "Yapıldı" veya "yapılmayacak" butonuna basıldı
            if result == 2:
                record_log(f"✅ Hatırlatıcı'{hatirlatici.not_metni}', uyarı penceresinde  'yapıldı' olarak seçildi")
            if hatirlatici.tekrarlama_tipi != "yok":
                # record_log(f"🔄 [HATIRLATICI DEBUG] Tekrarlı hatırlatıcı '{hatirlatici.not_metni}' için sonraki tekrar hesaplanıyor...")
                # Tekrarlayıcı için: sonraki tekrarı oluştur ve mevcut hatırlatıcıyı güncelle
                sonraki_tarih = hatirlatici.get_sonraki_tekrar_tarihi()
                # record_log(f"🔄 [HATIRLATICI DEBUG] Sonraki tekrar tarihi: {sonraki_tarih}")
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

            self.hatirlatici_listelerini_guncelle()
            self.uygulama.ayarlari_kaydet()
        else:
            record_log(f"⏱️ Hatırlatıcı '{hatirlatici.not_metni}' için 'Daha Sonra' seçildi")
            # "Daha Sonra" seçildiğinde erteleme flag'i ekle
            hatirlatici.ertelendi = True
            hatirlatici._ertelendi = True

            # Bildirim flag'ini temizle ki tekrar bildirim gelsin
            if hasattr(hatirlatici, '_bildirim_gosterildi'):
                delattr(hatirlatici, '_bildirim_gosterildi')
            
            self.hatirlatici_listelerini_guncelle()
            self.uygulama.ayarlari_kaydet()
                
    def hatirlatici_ses_cal(self, ses_dosyasi="ding-01.mp3"):
        """Hatırlatıcı için ses çal"""
        from PyQt5.QtCore import QUrl
        from PyQt5.QtMultimedia import QMediaContent
               
        dosya_yolu = os.path.join(self.uygulama.veri_klasoru, ses_dosyasi)
        
        # Dosya var mı kontrol et
        if not os.path.exists(dosya_yolu):
            # Varsayılan alarma dön
            dosya_yolu = os.path.join(self.uygulama.veri_klasoru, ses_dosyasi)
            if not os.path.exists(dosya_yolu):
                record_log(f"❗ Hatırlatıcı ses dosyası bulunamadı: {ses_dosyasi}", "error")
                return
        
        try:
            url = QUrl.fromLocalFile(dosya_yolu)
            content = QMediaContent(url)
            self.uygulama.medya_oynatici.setMedia(content)
            self.uygulama.medya_oynatici.play()
            # record_log(f"🎵 Hatırlatıcı sesi çalınıyor: {ses_dosyasi}")
        except Exception as e:
            record_log(f"❗ Hatırlatıcı sesi çalınırken hata: {str(e)}", "error")






