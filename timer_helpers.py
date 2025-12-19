import os
import json
import datetime
import sys
import tkinter as tk
from PyQt5.QtWidgets import QMessageBox, QDialog, QListWidgetItem, QLabel, QWidget, QHBoxLayout, QApplication, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QTime, QTimer
from PyQt5.QtGui import QFont, QColor 

class TimerHelpers:
    """Zamanlayıcı yardımcı metodları sınıfı"""
    
    def __init__(self, parent_app):
        self.app = parent_app
            
    # ========== FAVORİ YÖNETİMİ ==========
    def favoriye_ekle(self, gecmis_indeks):
        """Seçilen geçmiş kaydını favorilere ekle"""
        try:
            # QListWidget'tan seçili öğeyi al
            selected_items = self.app.gecmis_listesi_widget.selectedItems()
            if not selected_items:
                return
            
            selected_text = selected_items[0].text()
            
            # Metinden tarih bilgisini çıkar
            tarih_part = selected_text.split(' - ')[0]  # İlk ' - ' karakterine kadar olan kısım tarih
            
            # Orijinal listede bu tarihe sahip kaydı bul
            target_kayit = None
            for kayit in self.app.gecmis_listesi:
                if kayit['tarih'] == tarih_part:
                    target_kayit = kayit
                    break
            
            if not target_kayit:
                QMessageBox.warning(self.app, "Hata", "Seçilen geçmiş kaydı bulunamadı!")
                return
            
            # Aynı özelliklere sahip favori var mı kontrol et
            for favori in self.app.favori_listesi:
                if (favori['sure'] == target_kayit['sure'] and 
                    favori['aciklama'] == target_kayit['aciklama'] and
                    favori.get('alarm', 'alarm-01.mp3') == target_kayit.get('alarm', 'alarm-01.mp3')):
                    QMessageBox.information(self.app, "Bilgi", "Bu zamanlayıcı zaten favorilerde mevcut!")
                    return
            
            # Favorilere ekle
            yeni_favori = {
                'sure': target_kayit['sure'],
                'aciklama': target_kayit['aciklama'],
                'alarm': target_kayit.get('alarm', 'alarm-01.mp3'),
                'tekrar_toplam_sayi': target_kayit.get('tekrar_toplam_sayi', 1),
                'tekrar_araligi_dakika': target_kayit.get('tekrar_araligi_dakika', 10),
                'ozel_saat_aktif_ilk_calisma': target_kayit.get('ozel_saat_aktif_ilk_calisma', False),
                'ozel_saat_str': target_kayit.get('ozel_saat_str', None)
            }
            
            self.app.favori_listesi.append(yeni_favori)
            self.favori_listesini_guncelle()
            self.ayarlari_kaydet()
            
            QMessageBox.information(self.app, "Başarılı", "Geçmiş kaydı favorilere eklendi!")
            
        except Exception as e:
            QMessageBox.warning(self.app, "Hata", f"Favoriye eklenirken hata oluştu: {str(e)}")

    def favorileri_goster(self):
        """Favori listesini göster/gizle"""
        yeni_durum = not self.app.favori_listesi_widget.isVisible()
                
        self.app.favori_listesi_widget.setVisible(yeni_durum)
        # self.app.favori_sil_dugme.setVisible(yeni_durum)
        
        if yeni_durum:
            self.favori_listesini_guncelle()
            self.app.resize(500, 600)
            self.app.favori_dugme.setText("FAVORİLERİ GİZLE")
        else:
            self.app.resize(500, 400)
            self.app.favori_dugme.setText("FAVORİLER")

    def favori_listesini_guncelle(self):
        """Favori listesini güncelle"""
        self.app.favori_listesi_widget.clear()
        for favori in self.app.favori_listesi:
            alarm_bilgisi = ""
            if 'alarm' in favori and favori['alarm'] != "alarm-01.mp3":
                alarm_bilgisi = f" - Alarm: {favori['alarm']}"
            
            tekrar_bilgisi = ""
            if favori.get('tekrar_toplam_sayi', 1) > 1:
                tekrar_bilgisi = f" (Tekrar: {favori['tekrar_toplam_sayi']} kez, {favori.get('tekrar_araligi_dakika',10)} dk ara)"

            ozel_saat_bilgisi = ""
            if favori.get('ozel_saat_aktif_ilk_calisma') and favori.get('ozel_saat_str'):
                ozel_saat_bilgisi = f" - İlk Alarm: {favori['ozel_saat_str']}"

            self.app.favori_listesi_widget.addItem(
                f"⭐ {favori['sure']} dakika - {favori.get('aciklama', 'Açıklama yok')}{alarm_bilgisi}{tekrar_bilgisi}{ozel_saat_bilgisi}"
            )

    def favori_secimi_degisti(self):
        """Favori listesindeki seçim değiştiğinde silme düğmesini etkinleştir/devre dışı bırak"""
        self.app.favori_sil_dugme.setEnabled(len(self.app.favori_listesi_widget.selectedItems()) > 0)

    def favoriden_sil(self, favori_indeks):
        """Seçilen favoriyi sil"""
        try:
            if 0 <= favori_indeks < len(self.app.favori_listesi):
                favori = self.app.favori_listesi[favori_indeks]
                cevap = QMessageBox.question(
                    self.app,
                    "Favori Silme",
                    f"'{favori.get('aciklama', 'Bilinmeyen')}' favoriyi silmek istediğinizden emin misiniz?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if cevap == QMessageBox.Yes:
                    self.app.favori_listesi.pop(favori_indeks)
                    self.favori_listesini_guncelle()
                    self.ayarlari_kaydet()
        except Exception as e:
            QMessageBox.warning(self.app, "Hata", f"Favori silinirken hata oluştu: {str(e)}")

    def secilen_favorileri_sil(self):
        """Seçilen favorileri sil"""
        secili_ogelerin_indeksleri = []
        
        for item in self.app.favori_listesi_widget.selectedItems():
            secili_ogelerin_indeksleri.append(self.app.favori_listesi_widget.row(item))
        
        secili_sayi = len(secili_ogelerin_indeksleri)
        if secili_sayi == 0:
            return
        
        cevap = QMessageBox.question(
            self.app,
            "Favori Silme",
            f"Seçili {secili_sayi} favoriyi silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if cevap == QMessageBox.Yes:
            secili_ogelerin_indeksleri.sort(reverse=True)
            
            for indeks in secili_ogelerin_indeksleri:
                self.app.favori_listesi.pop(indeks)
                self.app.favori_listesi_widget.takeItem(indeks)
            
            self.ayarlari_kaydet()
            self.app.favori_sil_dugme.setEnabled(False)

    def favori_zamanlayici_baslat(self, item):
        """Favori zamanlayıcıyı başlat"""
        try:
            # Zamanlayici sınıfını globals'tan al
            import sys
            current_module = sys.modules['__main__']
            Zamanlayici = getattr(current_module, 'Zamanlayici')
            
            indeks = self.app.favori_listesi_widget.row(item)
            favori = self.app.favori_listesi[indeks]
            
            self.app.zamanlayici_id_sayaci += 1
            yeni_zamanlayici = Zamanlayici(
                id=self.app.zamanlayici_id_sayaci,
                dakika_ayari=favori['sure'],
                temel_aciklama=favori.get('aciklama', 'Zamanlayıcı'),
                alarm=favori.get('alarm', 'alarm-01.mp3'),
                tekrar_toplam_sayi=favori.get('tekrar_toplam_sayi', 1),
                tekrar_mevcut_calisma=1, 
                tekrar_araligi_dakika=favori.get('tekrar_araligi_dakika', 10),
                ozel_saat_aktif_ilk_calisma=favori.get('ozel_saat_aktif_ilk_calisma', False),
                ozel_saat_str=favori.get('ozel_saat_str', None)
            )

            yeni_zamanlayici.baslama_zamani_ilk_kurulum = datetime.datetime.now()

            # Süre hesaplama mantığı (normal veya özel saat)
            if yeni_zamanlayici.ozel_saat_aktif_ilk_calisma and yeni_zamanlayici.ozel_saat_str:
                # Özel saat mantığı (geçmiş zamanlayıcı başlatma ile aynı)
                try:
                    alarm_saati_qtime = QTime.fromString(yeni_zamanlayici.ozel_saat_str, "HH:mm")
                    simdiki_datetime = datetime.datetime.now()
                    alarm_hedef_datetime = datetime.datetime(
                        simdiki_datetime.year, simdiki_datetime.month, simdiki_datetime.day,
                        alarm_saati_qtime.hour(), alarm_saati_qtime.minute()
                    )
                    if alarm_hedef_datetime < simdiki_datetime:
                        alarm_hedef_datetime += datetime.timedelta(days=1)
                    fark_saniye = int((alarm_hedef_datetime - simdiki_datetime).total_seconds())
                    if fark_saniye < 0: fark_saniye = 0
                    yeni_zamanlayici.sure = fark_saniye
                    yeni_zamanlayici.toplam_sure = fark_saniye
                except Exception:
                    yeni_zamanlayici.sure = yeni_zamanlayici.dakika_ayari * 60
                    yeni_zamanlayici.toplam_sure = yeni_zamanlayici.dakika_ayari * 60
                    yeni_zamanlayici.ozel_saat_aktif_ilk_calisma = False
            else:
                # Normal dakika bazlı zamanlayıcı
                yeni_zamanlayici.sure = yeni_zamanlayici.dakika_ayari * 60
                yeni_zamanlayici.toplam_sure = yeni_zamanlayici.dakika_ayari * 60

            # Zamanlayıcıyı listeye ekle ve widget oluştur
            self.app.aktif_zamanlayicilar.append(yeni_zamanlayici)
            self.app.zamanlayici_widget_olustur(yeni_zamanlayici)
            self.app.son_sure = favori['sure']
            self.ayarlari_kaydet()
            
            # Favori listesini gizle ve ana arayüze odaklan
            # if self.app.favori_listesi_widget.isVisible():
            #     self.favorileri_goster()
            
        except Exception as e:
            QMessageBox.warning(self.app, "Hata", f"Favori zamanlayıcı başlatılırken hata oluştu: {str(e)}")

    def favori_duzenle(self, favori_indeks):
        """Seçilen favoriyi düzenle"""
        try:
            # Sınıfları globals'tan al
            import sys
            current_module = sys.modules['__main__']
            Zamanlayici = getattr(current_module, 'Zamanlayici')
            YeniZamanlayiciDialog = getattr(current_module, 'YeniZamanlayiciDialog')
                        
            if not (0 <= favori_indeks < len(self.app.favori_listesi)):
                QMessageBox.warning(self.app, "Hata", "Geçersiz favori seçimi!")
                return
            
            favori = self.app.favori_listesi[favori_indeks]
            
            # Favori verilerini zamanlayıcı formatına dönüştür
            temp_zamanlayici = Zamanlayici(
                id=999999,  # Geçici ID
                dakika_ayari=favori['sure'],
                temel_aciklama=favori.get('aciklama', 'Favori'),
                alarm=favori.get('alarm', 'alarm-01.mp3'),
                tekrar_toplam_sayi=favori.get('tekrar_toplam_sayi', 1),
                tekrar_mevcut_calisma=1,
                tekrar_araligi_dakika=favori.get('tekrar_araligi_dakika', 10),
                ozel_saat_aktif_ilk_calisma=favori.get('ozel_saat_aktif_ilk_calisma', False),
                ozel_saat_str=favori.get('ozel_saat_str', None)
            )
            
            # Düzenleme dialogunu aç
            dialog = YeniZamanlayiciDialog(
                self.app, 
                self.app.alarm_dosyalari, 
                varsayilan_sure=temp_zamanlayici.dakika_ayari,
                veri_klasoru=self.app.veri_klasoru,
                zamanlayici_to_edit=temp_zamanlayici,
                is_editing_favorite=True
            )
            
            if dialog.exec_() == QDialog.Accepted:
                values = dialog.getValues()
                
                # Güncellenmiş değerlerle favoriyi değiştir
                guncellenmis_favori = {
                    'sure': values['dakika'],
                    'aciklama': values['aciklama'],
                    'alarm': values['alarm'],
                    'tekrar_toplam_sayi': values['tekrar_sayisi'],
                    'tekrar_araligi_dakika': values['tekrar_araligi_dakika'],
                    'ozel_saat_aktif_ilk_calisma': values['alarm_zamani_aktif'],
                    'ozel_saat_str': values['alarm_zamani'] if values['alarm_zamani_aktif'] else None
                }
                
                # Favoriyi güncelle
                self.app.favori_listesi[favori_indeks] = guncellenmis_favori
                
                # Arayüzü güncelle
                self.favori_listesini_guncelle()
                
                # Ayarları kaydet
                self.ayarlari_kaydet()
                
                QMessageBox.information(self.app, "Başarılı", "Favori başarıyla güncellendi!")
                
        except Exception as e:
            QMessageBox.warning(self.app, "Hata", f"Favori düzenlenirken hata oluştu: {str(e)}")

    # ========== GEÇMİŞ YÖNETİMİ ==========
    def gecmis_secimi_degisti(self):
        """Geçmiş listesindeki seçim değiştiğinde silme düğmesini etkinleştir/devre dışı bırak"""
        self.app.sil_dugme.setEnabled(len(self.app.gecmis_listesi_widget.selectedItems()) > 0)
    
    def secilen_gecmisi_sil(self):
        """Seçilen geçmiş kayıtlarını sil"""
        selected_items = self.app.gecmis_listesi_widget.selectedItems()
        if not selected_items:
            return
        
        # Seçili öğelerin gerçek metinlerini al
        selected_texts = [item.text() for item in selected_items]
        
        secili_sayi = len(selected_texts)        
        
        # Silinecek kayıtların detaylarını topla
        silinecek_kayitlar = []
        indices_to_remove = []
        
        for selected_text in selected_texts:
            # Metinden tarih bilgisini çıkar
            tarih_part = selected_text.split(' - ')[0]  # İlk ' - ' karakterine kadar olan kısım tarih
            
            # Orijinal listede bu tarihe sahip kaydı bul
            for i, kayit in enumerate(self.app.gecmis_listesi):
                if kayit['tarih'] == tarih_part and i not in indices_to_remove:
                    indices_to_remove.append(i)
                    silinecek_kayitlar.append({
                        'tarih': kayit['tarih'],
                        'aciklama': kayit.get('aciklama', 'Açıklama yok'),
                        'sure': kayit['sure']
                    })
                    break  # Aynı tarihe sahip birden fazla kayıt varsa sadece ilkini al
        
        # Detaylı onay mesajı oluştur
        if secili_sayi == 1:
            kayit = silinecek_kayitlar[0]
            mesaj = f"Aşağıdaki geçmiş kaydını silmek istediğinizden emin misiniz?\n\n"
            mesaj += f"📅 Tarih: {kayit['tarih']}\n"
            mesaj += f"⏱️ Süre: {kayit['sure']} dakika\n"
            mesaj += f"📝 Açıklama: {kayit['aciklama']}"
        else:
            mesaj = f"Aşağıdaki {secili_sayi} geçmiş kaydını silmek istediğinizden emin misiniz?\n\n"
            for i, kayit in enumerate(silinecek_kayitlar, 1):
                mesaj += f"{i}. 📅 {kayit['tarih']} - ⏱️ {kayit['sure']} dk - 📝 {kayit['aciklama']}\n"
        
        cevap = QMessageBox.question(
            self.app,
            "Geçmiş Kaydı Silme",
            mesaj,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if cevap == QMessageBox.Yes:
            # Seçili metinlere karşılık gelen orijinal kayıtları bul ve sil
            indices_to_remove = []
            
            for selected_text in selected_texts:
                # Metinden tarih bilgisini çıkar
                tarih_part = selected_text.split(' - ')[0]  # İlk ' - ' karakterine kadar olan kısım tarih
                
                # Orijinal listede bu tarihe sahip kayıtları bul
                for i, kayit in enumerate(self.app.gecmis_listesi):
                    if kayit['tarih'] == tarih_part and i not in indices_to_remove:
                        indices_to_remove.append(i)
                        break  # Aynı tarihe sahip birden fazla kayıt varsa sadece ilkini al
            
            # İndeksleri ters sırada sil (listenin bozulmasını önlemek için)
            for index in sorted(indices_to_remove, reverse=True):
                if 0 <= index < len(self.app.gecmis_listesi):
                    self.app.gecmis_listesi.pop(index)
            
            # Ayarları kaydet
            self.ayarlari_kaydet()
            self.app.sil_dugme.setEnabled(len(self.app.gecmis_listesi_widget.selectedItems()) > 0)
            # Geçmiş listesini yeniden yükle
            self.gecmisi_goster(force_refresh_only_if_visible=True)
            
            print(f"DEBUG: {secili_sayi} kayıt silindi. Kalan kayıt sayısı: {len(self.app.gecmis_listesi)}")

    def gecmisi_goster(self, force_refresh_only_if_visible=False):
        """
        Geçmiş listesini göster/gizle.
        Eğer force_refresh_only_if_visible True ise ve liste görünür durumdaysa, sadece içeriği yeniler.
        """
        
        # İçeriği doldurmak için yardımcı fonksiyon (kod tekrarını önlemek için)
        def _populate_content():
            self.app.gecmis_listesi_widget.clear()
            try:
                # Geçmiş listesini tarihe göre tersten sırala (en yeni en üstte)
                sorted_gecmis = sorted(
                    self.app.gecmis_listesi,
                    key=lambda x: datetime.datetime.strptime(x['tarih'], '%d.%m.%Y %H:%M:%S'),
                    reverse=True
                )
            except (ValueError, KeyError, TypeError) as e:
                print(f"Uyarı: Geçmiş sıralanamadı. Olduğu gibi gösteriliyor. Hata: {e}, Liste: {self.app.gecmis_listesi}")
                sorted_gecmis = self.app.gecmis_listesi

            for kayit in sorted_gecmis:
                alarm_bilgisi = ""
                if 'alarm' in kayit and kayit['alarm'] != "alarm-01.mp3":
                    alarm_bilgisi = f" - Alarm: {kayit['alarm']}"
                
                tekrar_bilgisi = ""
                if kayit.get('tekrar_toplam_sayi', 1) > 1:
                    tekrar_bilgisi = f" (Tekrar: {kayit['tekrar_toplam_sayi']} kez, {kayit.get('tekrar_araligi_dakika',10)} dk ara)"

                ozel_saat_bilgisi = ""
                if kayit.get('ozel_saat_aktif_ilk_calisma') and kayit.get('ozel_saat_str'):
                    ozel_saat_bilgisi = f" - İlk Alarm: {kayit['ozel_saat_str']}"
                
                item_text = f"{kayit['tarih']} - {kayit['sure']} dakika - {kayit.get('aciklama', 'Açıklama yok')}{alarm_bilgisi}{tekrar_bilgisi}{ozel_saat_bilgisi}"
                list_item = QListWidgetItem(item_text)
                

                self.app.gecmis_listesi_widget.addItem(list_item)

            self.app.sil_dugme.setEnabled(False) # İçerik yenilendiğinde başlangıçta hiçbir öğe seçili olmaz

        if force_refresh_only_if_visible and self.app.gecmis_listesi_widget.isVisible():
            _populate_content()
            # Burada görünürlüğü, buton metnini veya boyutu değiştirme
            return

        # Orijinal görünürlük değiştirme mantığı
        yeni_durum = not self.app.gecmis_listesi_widget.isVisible()
        self.app.gecmis_listesi_widget.setVisible(yeni_durum)
        
        if yeni_durum: # Panel şimdi görünür
            _populate_content()
            self.app.resize(500, 600) # Kullanıcının orijinal boyutlandırması
            # self.app.sil_dugme.setEnabled(False) # _populate_content içinde zaten yapıldı
            self.app.gecmis_dugme.setText("GEÇMİŞİ GİZLE")
        else: # Panel şimdi gizli
            self.app.resize(500, 400) # Kullanıcının orijinal boyutlandırması
            self.app.gecmis_dugme.setText("GEÇMİŞ")
            self.app.sil_dugme.setEnabled(False) # Gizliyken silme butonu devre dışı olmalı

    def gecmis_zamanlayici_baslat(self, item):
        """Geçmiş listesinden zamanlayıcı başlat (çift tıklama) - Doğrudan başlat"""
        try:
            # Seçili öğenin metnini al
            selected_text = item.text()
            
            # Metinden tarih bilgisini çıkar
            tarih_part = selected_text.split(' - ')[0]  # İlk ' - ' karakterine kadar olan kısım tarih
            
            # Orijinal listede bu tarihe sahip kaydı bul
            target_kayit = None
            for kayit in self.app.gecmis_listesi:
                if kayit['tarih'] == tarih_part:
                    target_kayit = kayit
                    break
            
            if not target_kayit:
                QMessageBox.warning(self.app, "Hata", "Seçilen geçmiş kaydı bulunamadı!")
                return
            
            # Zamanlayici sınıfını globals'tan al
            current_module = sys.modules['__main__']
            Zamanlayici = getattr(current_module, 'Zamanlayici')
            
            # Yeni zamanlayıcıyı doğrudan oluştur ve başlat
            self.app.zamanlayici_id_sayaci += 1
            yeni_zamanlayici = Zamanlayici(
                id=self.app.zamanlayici_id_sayaci, 
                dakika_ayari=target_kayit['sure'], 
                temel_aciklama=target_kayit.get('aciklama', 'Geçmişten'),
                alarm=target_kayit.get('alarm', 'alarm-01.mp3'),
                tekrar_toplam_sayi=target_kayit.get('tekrar_toplam_sayi', 1),
                tekrar_mevcut_calisma=1, 
                tekrar_araligi_dakika=target_kayit.get('tekrar_araligi_dakika', 10),
                ozel_saat_aktif_ilk_calisma=target_kayit.get('ozel_saat_aktif_ilk_calisma', False),
                ozel_saat_str=target_kayit.get('ozel_saat_str', None)
            )
            yeni_zamanlayici.baslama_zamani_ilk_kurulum = datetime.datetime.now()

            # Süre hesaplama mantığı (normal veya özel saat)
            if yeni_zamanlayici.ozel_saat_aktif_ilk_calisma and yeni_zamanlayici.ozel_saat_str:
                try:
                    alarm_saati_qtime = QTime.fromString(yeni_zamanlayici.ozel_saat_str, "HH:mm")
                    simdiki_datetime = datetime.datetime.now()
                    alarm_hedef_datetime = datetime.datetime(
                        simdiki_datetime.year, simdiki_datetime.month, simdiki_datetime.day,
                        alarm_saati_qtime.hour(), alarm_saati_qtime.minute()
                    )
                    if alarm_hedef_datetime < simdiki_datetime:
                        alarm_hedef_datetime += datetime.timedelta(days=1)
                    fark_saniye = int((alarm_hedef_datetime - simdiki_datetime).total_seconds())
                    if fark_saniye < 0: fark_saniye = 0
                    yeni_zamanlayici.sure = fark_saniye
                    yeni_zamanlayici.toplam_sure = fark_saniye
                except Exception:
                    yeni_zamanlayici.sure = yeni_zamanlayici.dakika_ayari * 60
                    yeni_zamanlayici.toplam_sure = yeni_zamanlayici.dakika_ayari * 60
                    yeni_zamanlayici.ozel_saat_aktif_ilk_calisma = False
            else:
                yeni_zamanlayici.sure = yeni_zamanlayici.dakika_ayari * 60
                yeni_zamanlayici.toplam_sure = yeni_zamanlayici.dakika_ayari * 60

            # Zamanlayıcıyı listeye ekle ve widget oluştur
            self.app.aktif_zamanlayicilar.append(yeni_zamanlayici)
            self.app.zamanlayici_widget_olustur(yeni_zamanlayici)
            self.app.son_sure = target_kayit['sure']
            self.ayarlari_kaydet()
            
            # # Ctrl tuşuna basılıysa panel açık kalsın, değilse kapansın
            # from PyQt5.QtWidgets import QApplication
            # modifiers = QApplication.keyboardModifiers()
            # from PyQt5.QtCore import Qt
            
            # if not (modifiers & Qt.ControlModifier):
            #     if self.app.gecmis_listesi_widget.isVisible():
            #         self.gecmisi_goster()            
            
        except Exception as e:
            QMessageBox.warning(self.app, "Hata", f"Geçmiş zamanlayıcı başlatılırken hata oluştu: {str(e)}")

    # ========== AYAR YÖNETİMİ ==========
    def ayarlari_kaydet(self):
        """Ayarları ve aktif zamanlayıcıları kaydet"""
        veri = {
            'son_sure': self.app.son_sure,
            'gecmis': self.app.gecmis_listesi,
            'favoriler': self.app.favori_listesi,
            'zamanlayici_id_sayaci': self.app.zamanlayici_id_sayaci,
            'hatirlaticilar': [h.to_dict() for h in self.app.hatirlaticilar],
            'hatirlatici_id_sayaci': self.app.hatirlatici_id_sayaci,
            'aktif_zamanlayicilar': [z.to_dict() for z in self.app.aktif_zamanlayicilar],
            'aktif_kronometreler': [k.to_dict() for k in self.app.aktif_kronometreler],
            'kronometre_id_sayaci': self.app.kronometre_id_sayaci
        }
        
        try:
            with open(self.app.veri_dosyasi, 'w', encoding='utf-8') as dosya:
                json.dump(veri, dosya, ensure_ascii=False)
            # print("Ayarlar ve aktif zamanlayıcılar başarıyla kaydedildi.")
        except Exception as e:
            print(f"Ayarlar helper tarafından kaydedilemedi: {str(e)}")

    # ========== LOG YÖNEETİMİ ==========
    def loglari_goster_DEPRECIATED(self):
        """Logları göster"""
        try:
            if not os.path.exists(self.app.log_dosyasi):
                QMessageBox.information(self.app, "Bilgi", "Log dosyasına erişilemiyor.")
                return
            
            with open(self.app.log_dosyasi, 'r', encoding='utf-8') as dosya:
                log_icerigi = dosya.read()
            
            # Log içeriğini yeni bir pencere içinde göster
            log_pencere = QWidget()
            log_pencere.setWindowTitle("Log Kayıtları")
            layout = QHBoxLayout()
            log_label = QLabel(log_icerigi)
            log_label.setFont(QFont("Courier New", 10))
            layout.addWidget(log_label)
            log_pencere.setLayout(layout)
            log_pencere.resize(600, 400)
            log_pencere.show()
        except Exception as e:
            QMessageBox.warning(self.app, "Hata", f"Loglar gösterilirken hata oluştu: {str(e)}")


active_toasts = []

def show_toast(parent, msgTime, message, duration=2000):
    global active_toasts

    toast = QWidget(parent)
    toast.setWindowFlags(Qt.ToolTip)
    background_color= "#fadfc1"  # Turuncu arka plan
    toast.setStyleSheet(f"""
        background-color: {background_color}; 
        border-radius: 16px;
    """)
    layout = QVBoxLayout(toast)
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(15)

    msg_time = QLabel(msgTime)
    msg_time.setAlignment(Qt.AlignCenter)
    msg_time.setFont(QFont("Arial", 12, QFont.Bold))
    layout.addWidget(msg_time)

    # Ortalı, büyük ve renkli label
    # simdi = datetime.datetime.now()
    # simdi = simdi.strftime("%H:%M:%S")
    # message = simdi + ": " + message
    msg = QLabel(message)
    msg.setAlignment(Qt.AlignCenter)
    msg.setFont(QFont("Arial", 16, QFont.Bold))
    font_color = "#ff9718"
    msg.setStyleSheet(f"color: {font_color};")  
    layout.addWidget(msg)
    
    button = QPushButton("Kapat")
    button.clicked.connect(toast.close)
    button.setCursor(Qt.PointingHandCursor)    
    layout.addWidget(button)

    toast.setMinimumWidth(400)
    toast.setMinimumHeight(100)
    toast.adjustSize()

    # Ekranın sağ alt köşesine yerleştir
    screen = parent.screen() if hasattr(parent, "screen") else QApplication.primaryScreen()
    screen_geometry = screen.availableGeometry()
    margin = 30
    spacing = 10
    toast_height = toast.height() + spacing

    # Kaç tane açık toast var, ona göre yukarı kaydır
    n = len(active_toasts)
    x = screen_geometry.right() - toast.width() - margin
    y = screen_geometry.bottom() - toast.height() - margin - n * toast_height

    toast.move(x- 10, y)
    toast.show()

    active_toasts.append(toast)

    # Kapatıldığında listeden çıkar ve kalanları yeniden hizala
    def closeEvent(event):
        try:
            active_toasts.remove(toast)
        except ValueError:
            pass
        # Kapanınca alttakileri yeniden hizala
        for idx, t in enumerate(active_toasts):
            new_y = screen_geometry.bottom() - t.height() - margin - idx * toast_height
            t.move(x, new_y)
        event.accept()
        # print(f"DEBUG: Kalan toast sayısı: {len(active_toasts)}")
    toast.closeEvent = closeEvent

    if duration > 0:
        # Toast'u belirli bir süre sonra kapat
        toast.setAttribute(Qt.WA_DeleteOnClose)
        QTimer.singleShot(duration, toast.close)

