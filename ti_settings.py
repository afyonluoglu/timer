"""
Ayarların, pencere splitter durumunun ve alarm dosyalarının yüklenip kaydedilmesini sağlayan Mixin modülü.
"""

import os
import json
import glob
import datetime
from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog

from ti_models import Kronometre, Zamanlayici, VARSAYILAN_ALARM_DOSYASI
from timer_reminder_system import Hatirlatici
from timer_formatter import format_time
from timer_logger import record_log
from timer_helpers import show_toast
from ti_dialogs import FavoriGeriYukleDialog


class SettingsMixin:
    """Uygulama ayarlarını, aktif zamanlayıcı/kronometre durumlarını ve dosya yollarını yöneten Mixin."""

    def alarm_dosyalarini_bul(self):
        """Timer-data klasöründeki tüm .mp3 dosyalarını bulur"""
        try:
            self.alarm_dosyalari = []
            alarm_klasoru = self.veri_klasoru
            if os.path.exists(alarm_klasoru):
                for dosya_adi in sorted(os.listdir(alarm_klasoru), key=str.lower):
                    tam_yol = os.path.join(alarm_klasoru, dosya_adi)
                    if os.path.isfile(tam_yol) and dosya_adi.lower().endswith(".mp3"):
                        self.alarm_dosyalari.append(dosya_adi)

            if VARSAYILAN_ALARM_DOSYASI not in self.alarm_dosyalari:
                record_log(f"❗ Uyarı: Varsayılan alarm dosyası ({VARSAYILAN_ALARM_DOSYASI}) bulunamadı!", "error")
        except Exception as e:
            record_log(f"Alarm dosyaları taranırken hata: {str(e)}", "error")
            self.alarm_dosyalari = []

    def ayarlari_kaydet(self):
        """Ayarları kaydeder (yardımcı sınıf üzerinden delege edilir)"""
        return self.helpers.ayarlari_kaydet()

    def splitter_pozisyonu_kaydet(self, pos=None, index=None):
        """Tüm splitter pozisyonlarını kaydet"""
        try:
            ana_splitter_pozisyonu = self.ana_bolum_splitter.sizes()
            hatirlatici_splitter_pozisyonu = self.hatirlatici_splitter.sizes()

            ayarlar = {}
            if os.path.exists(self.veri_dosyasi):
                with open(self.veri_dosyasi, 'r', encoding='utf-8') as dosya:
                    ayarlar = json.load(dosya)

            ayarlar['splitter_pozisyonu'] = ana_splitter_pozisyonu
            ayarlar['hatirlatici_splitter_pozisyonu'] = hatirlatici_splitter_pozisyonu

            with open(self.veri_dosyasi, 'w', encoding='utf-8') as dosya:
                json.dump(ayarlar, dosya, ensure_ascii=False)
        except Exception as e:
            record_log(f"Splitter pozisyonu kaydedilemedi: {str(e)}", "error")

    def splitter_pozisyonu_yukle(self):
        """Tüm splitter pozisyonlarını yükle"""
        try:
            if os.path.exists(self.veri_dosyasi):
                with open(self.veri_dosyasi, 'r', encoding='utf-8') as dosya:
                    veri = json.load(dosya)
                    if 'splitter_pozisyonu' in veri:
                        self.ana_bolum_splitter.setSizes(veri['splitter_pozisyonu'])
                    if 'hatirlatici_splitter_pozisyonu' in veri:
                        self.hatirlatici_splitter.setSizes(veri['hatirlatici_splitter_pozisyonu'])
        except Exception as e:
            record_log(f"Splitter pozisyonu yüklenemedi: {str(e)}", "error")

    def ayarlari_yukle(self):
        """Ayarları ve aktif zamanlayıcıları yükle"""
        try:
            if os.path.exists(self.veri_dosyasi):
                with open(self.veri_dosyasi, 'r', encoding='utf-8') as dosya:
                    veri = json.load(dosya)
                    self.son_sure = veri.get('son_sure', 5)
                    self.gecmis_listesi = veri.get('gecmis', [])
                    self.favori_listesi = veri.get('favoriler', [])
                    self.zamanlayici_id_sayaci = veri.get('zamanlayici_id_sayaci', 0)

                    if 'hatirlaticilar' in veri:
                        self.hatirlaticilar = [Hatirlatici.from_dict(h) for h in veri['hatirlaticilar']]
                    else:
                        self.hatirlaticilar = []

                    self.hatirlatici_id_sayaci = veri.get('hatirlatici_id_sayaci', 0)

                    if 'aktif_zamanlayicilar' in veri:
                        simdi = datetime.datetime.now()
                        for z_veri in veri['aktif_zamanlayicilar']:
                            try:
                                z = Zamanlayici.from_dict(z_veri)

                                if z.ozel_saat_aktif_ilk_calisma and z.tekrar_mevcut_calisma == 1:
                                    hedef_saati_qtime = QTime.fromString(z.ozel_saat_str, "HH:mm")
                                    hedef_saati_dt = datetime.time(hedef_saati_qtime.hour(), hedef_saati_qtime.minute())

                                    hedef_datetime_planlanan = datetime.datetime.combine(
                                        z.baslama_zamani_ilk_kurulum.date(), 
                                        hedef_saati_dt
                                    )
                                    if hedef_datetime_planlanan < z.baslama_zamani_ilk_kurulum:
                                        hedef_datetime_planlanan += datetime.timedelta(days=1)

                                    kalan_saniye_simdiye_gore = (hedef_datetime_planlanan - simdi).total_seconds()
                                    if kalan_saniye_simdiye_gore > 0:
                                        z.sure = int(kalan_saniye_simdiye_gore)
                                        z.toplam_sure = int((hedef_datetime_planlanan - z.baslama_zamani_ilk_kurulum).total_seconds())
                                        if z.toplam_sure < 0:
                                            z.toplam_sure = 0

                                        self.aktif_zamanlayicilar.append(z)
                                        self.zamanlayici_widget_olustur(z)
                                        record_log(f"✅ [YÜKLE] Özel saatli Timer (ilk alarm) ekleniyor: {z.id} - '{z.temel_aciklama}', Kalan süre: {format_time(z.sure)}, Toplam süre: {format_time(z.toplam_sure)}")
                                    else:
                                        self.gecmis_listesi.append({
                                            'tarih': hedef_datetime_planlanan.strftime('%d.%m.%Y %H:%M:%S'),
                                            'sure': z.dakika_ayari,
                                            'aciklama': z.temel_aciklama + " (Özel saatli alarm program kapalıyken tamamlandı)",
                                            'alarm': z.alarm_dosyasi,
                                            'tekrar_toplam_sayi': z.tekrar_toplam_sayi,
                                            'tekrar_mevcut_calisma': z.tekrar_mevcut_calisma, 
                                            'tekrar_araligi_dakika': z.tekrar_araligi_dakika,
                                            'ozel_saat_aktif_ilk_calisma': True,
                                            'ozel_saat_str': z.ozel_saat_str
                                        })
                                        record_log(f"➖ [YÜKLE] Özel saatli Timer (ilk alarm) süresi dolmuş, geçmişe ekleniyor: {z.id} - '{z.temel_aciklama}', Kalan süre: {format_time(z.sure)}, Toplam süre: {z.toplam_sure}")
                                else:
                                    if 'son_guncelleme_zamani' in z_veri:
                                        try:
                                            son_guncelleme = datetime.datetime.fromisoformat(z_veri['son_guncelleme_zamani'])
                                            gecen_sure = int((simdi - son_guncelleme).total_seconds())
                                            z.sure = max(0, z.sure - gecen_sure)
                                        except Exception as e:
                                            record_log(f"Zaman hesaplama hatası: {e}", "error")
                                    else:
                                        record_log(f"❗ [UYARI] Timer {z.id} - '{z.temel_aciklama}': son_guncelleme_zamani bulunamadı, süre düşürülmeyecek", "warning")

                                    record_log("⏰ Tamamlanmamış alarmlar için kalan süre hesaplanıyor...")    
                                    if z.sure > 0:
                                        if z.tekrar_mevcut_calisma > 1 and z.toplam_sure != z.dakika_ayari * 60:
                                            z.toplam_sure = z.dakika_ayari * 60
                                            if z.sure > z.toplam_sure:
                                                z.sure = z.toplam_sure
                                        record_log(f"✅ [YÜKLE] Timer {z.id} - '{z.temel_aciklama}': Zamanlayıcı aktif olarak ekleniyor, kalan süre: {format_time(z.sure)}")
                                        self.aktif_zamanlayicilar.append(z)
                                        self.zamanlayici_widget_olustur(z)
                                    else:
                                        record_log(f"➖ [YÜKLE] Timer {z.id} - '{z.temel_aciklama}': Süre dolmuş, geçmişe ekleniyor", "warning")
                                        show_toast(self, "Süresi Dolan Zamanlayıcı", f"{z.temel_aciklama}", duration=0)
                                        self.gecmis_listesi.append({
                                            'tarih': simdi.strftime('%d.%m.%Y %H:%M:%S'),
                                            'sure': z.dakika_ayari,
                                            'aciklama': z.temel_aciklama + " (Program kapalıyken tamamlandı)",
                                            'alarm': z.alarm_dosyasi,
                                            'tekrar_toplam_sayi': z.tekrar_toplam_sayi,
                                            'tekrar_mevcut_calisma': z.tekrar_mevcut_calisma,
                                            'tekrar_araligi_dakika': z.tekrar_araligi_dakika,
                                            'ozel_saat_aktif_ilk_calisma': z.ozel_saat_aktif_ilk_calisma,
                                            'ozel_saat_str': z.ozel_saat_str
                                        })
                                        record_log(f"🚩 Normal Zamanlayıcı geçmişe eklendi: {z.id} - {z.temel_aciklama} , Kalan süre: {format_time(z.sure)}, Toplam süre: {format_time(z.toplam_sure)}")

                            except Exception as e:
                                record_log(f"❗ Zamanlayıcı yüklenirken hata (iç döngü): {str(e)} - Veri: {z_veri}", "error")

                    self.kronometre_id_sayaci = veri.get('kronometre_id_sayaci', 0)
                    if 'aktif_kronometreler' in veri:
                        for k_veri in veri['aktif_kronometreler']:
                            try:
                                k = Kronometre.from_dict(k_veri)
                                self.aktif_kronometreler.append(k)
                                self.kronometre_widget_olustur(k)
                                record_log(f"⏱️ [YÜKLE] Kronometre '{k.isim}' yüklendi, geçen süre: {k.get_formatted_time()}")
                            except Exception as e:
                                record_log(f"❗ Kronometre yüklenirken hata: {str(e)} - Veri: {k_veri}", "error")
            else:
                self.son_sure = 5
                self.gecmis_listesi = []
                self.favori_listesi = []

            self.hatirlatici_manager.hatirlatici_listelerini_guncelle()
            self.splitter_pozisyonu_yukle()
        except Exception as e:
            record_log(f"❗ Ayarlar yüklenemedi (dış döngü): {str(e)}", "error")
            self.son_sure = 5
            self.gecmis_listesi = []
            self.favori_listesi = []

    def favori_yedekle(self):
        """Favori zamanlayıcı kayıtlarını timer-data klasörüne JSON formatında yedekler"""
        if not hasattr(self, 'favori_listesi') or not self.favori_listesi:
            QMessageBox.warning(self, "Uyarı", "Yedeklenecek favori zamanlayıcı kaydı bulunmuyor.")
            return

        tarih_str = datetime.datetime.now().strftime("%Y_%m_%d")
        dosya_adi = f"{tarih_str}_favorites_backup.json"
        dosya_yolu = os.path.join(self.veri_klasoru, dosya_adi)

        if os.path.exists(dosya_yolu):
            cevap = QMessageBox.question(
                self,
                "Yedek Dosyası Mevcut",
                f"'{dosya_adi}' dosyası zaten mevcut.\nÜzerine yazmak istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if cevap != QMessageBox.Yes:
                return

        try:
            with open(dosya_yolu, 'w', encoding='utf-8') as f:
                json.dump(self.favori_listesi, f, ensure_ascii=False, indent=4)
            record_log(f"Favoriler yedeklendi: {dosya_adi} ({len(self.favori_listesi)} adet)")
            QMessageBox.information(
                self,
                "Yedekleme Başarılı",
                f"Favori kayıtları başarıyla yedeklendi:\n{dosya_adi}\n\nToplam: {len(self.favori_listesi)} adet favori."
            )
        except Exception as e:
            record_log(f"Favori yedekleme hatası: {str(e)}", "error")
            QMessageBox.critical(self, "Hata", f"Yedekleme sırasında hata oluştu:\n{str(e)}")

    def favori_yedekten_geri_don(self):
        """Seçilen JSON yedek dosyasındaki favorileri önizleme penceresinde listeler ve onaylanırsa geri yükler"""
        dosya_yolu, _ = QFileDialog.getOpenFileName(
            self,
            "Favori Yedek Dosyası Seç",
            self.veri_klasoru,
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*)"
        )
        if not dosya_yolu:
            return

        try:
            with open(dosya_yolu, 'r', encoding='utf-8') as f:
                veri = json.load(f)
        except Exception as e:
            record_log(f"Yedek dosyası okuma hatası: {str(e)}", "error")
            QMessageBox.critical(self, "Hata", f"Yedek dosyası okunamadı:\n{str(e)}")
            return

        if isinstance(veri, list):
            yuklenen_favoriler = veri
        elif isinstance(veri, dict):
            yuklenen_favoriler = veri.get('favoriler') or veri.get('favorites') or []
        else:
            yuklenen_favoriler = []

        if not yuklenen_favoriler or not isinstance(yuklenen_favoriler, list):
            QMessageBox.warning(self, "Uyarı", "Seçilen dosyada geçerli favori zamanlayıcı kaydı bulunamadı.")
            return

        dialog = FavoriGeriYukleDialog(yuklenen_favoriler, os.path.basename(dosya_yolu), self)
        if dialog.exec_() == QDialog.Accepted:
            self.favori_listesi = list(yuklenen_favoriler)
            self.favori_listesini_guncelle()
            self.ayarlari_kaydet()
            record_log(f"Favoriler yedekten geri yüklendi: {os.path.basename(dosya_yolu)} ({len(yuklenen_favoriler)} adet)")
            QMessageBox.information(
                self,
                "Geri Yükleme Başarılı",
                f"Favori kayıtları başarıyla geri yüklendi!\n({len(yuklenen_favoriler)} adet favori)"
            )

