# ============================
# TIMER-01.PY
# Gereken Python Sürümü: 3.8 veya üzeri
# ============================

import sys
import os
import datetime
import random

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMessageBox, QFrame,
    QDialog, QMenu, QLabel, QPushButton
)
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtMultimedia import QMediaPlayer

from timer_helpers import TimerHelpers, show_toast
from dialog_classes import YeniZamanlayiciDialog, AlarmDialog
from timer_formatter import format_time, get_current_datetime_string
from timer_logger import setup_logging, record_log, VERI_KLASORU, LOG_DOSYASI
from timer_reminder_system import Hatirlatici
from timer_reminder_ui import HatirlaticiManager

# Modülerleştirilmiş Mixin ve Modeller
from ti_models import Kronometre, Zamanlayici, VARSAYILAN_ALARM_DOSYASI
from ti_natural_parser import parse_natural_timer
from ti_stopwatch import KronometreMixin
from ti_timer_widgets import TimerWidgetsMixin
from ti_settings import SettingsMixin
from ti_ui_builder import UIBuilderMixin
from ti_app_window import AnaUygulamaPenceresi


class ZamanlayiciUygulamasi(UIBuilderMixin, KronometreMixin, TimerWidgetsMixin, SettingsMixin, QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zamanlayıcı")
        self.resize(500, 600)

        # Timer data klasörünü oluştur
        self.veri_klasoru = VERI_KLASORU
        self.veri_dosyasi = os.path.join(self.veri_klasoru, "zamanlayici_ayarlar.json")
        self.log_dosyasi = LOG_DOSYASI

        self.hatirlatici_manager = HatirlaticiManager(self)
        os.makedirs(self.veri_klasoru, exist_ok=True)

        # Favori sistemi için değişkenler
        self.favori_listesi = []

        # Zamanlayıcı değişkenleri
        self.kalan_sure = 0
        self.calisma_durumu = False
        self.gecmis_listesi = []
        self.aktif_zamanlayicilar = []
        self.zamanlayici_id_sayaci = 0
        self.son_sure = 5

        # Hatırlatıcı değişkenleri
        self.hatirlaticilar = []
        self.hatirlatici_id_sayaci = 0

        # Kronometre değişkenleri
        self.aktif_kronometreler = []
        self.kronometre_id_sayaci = 0

        # Helper sınıfını başlat
        self.helpers = TimerHelpers(self)

        # Alarm dosyalarını bul
        self.alarm_dosyalarini_bul()

        # Önce arayüzü oluştur
        self.arayuzu_olustur()

        # Klavye kısayollarını ayarla
        self.kisayol_tuslari_ayarla()

        # Sonra ayarları yükle ve zamanlayıcıları başlat
        self.ayarlari_yukle()

        # Açılışta listeleri güncelle
        self.gecmisi_goster()
        self.favori_listesini_guncelle()

        # Medya oynatıcı
        self.medya_oynatici = QMediaPlayer()

        # Zamanlayıcı
        self.timer = QTimer()
        self.timer.timeout.connect(self.zamanlayici_guncelle)
        self.timer.setInterval(1000)
        self.timer.start(1000)

    def natural_language_timer(self):
        """Doğal dilde girilen komutu ayrıştırarak hatırlatıcı oluşturur."""
        text = self.natural_input.text()
        params = parse_natural_timer(text)
        if not params:
            QMessageBox.warning(self, "Hatalı Komut", "Doğal dil komutu anlaşılamadı. Lütfen örneğe uygun girin.")
            return

        print("☑️✅ Doğal dil komutu:", params)

        hatir_date = None
        hatir_time = None

        full_datetime = params.get("zaman") or params.get("tarih")
        if isinstance(full_datetime, datetime.datetime):
            hatir_date = full_datetime.date()
            hatir_time = full_datetime.time()
        elif params.get("alarm_zamani"):
            try:
                saat_str = params["alarm_zamani"]
                saat, dakika = map(int, saat_str.split(':'))
                hatir_time = datetime.time(saat, dakika)
                hatir_date = datetime.date.today()
            except (ValueError, TypeError):
                print("Hata: Alarm zamanı ayrıştırılamadı.")
                hatir_time = None

        if hatir_date is None or hatir_time is None:
            QMessageBox.warning(self, "Mantık Hatası", "Hatırlatıcı için geçerli bir zaman belirlenemedi.")
            return

        self.hatirlatici_id_sayaci += 1
        aciklama = params["aciklama"]

        tarih = None
        tekrar_tipi = None

        if params["tekrar_tipi"] == "her_gun":
            tekrar_tipi = "gun"
        elif params["tekrar_tipi"] == "her_hafta":
            tekrar_tipi = "hafta"
        elif params["tekrar_tipi"] == "her_ay":
            tekrar_tipi = "ay"
        elif params["tekrar_tipi"] == "aralikli":
            tekrar_tipi = "yok"
        elif params["tarih"]:
            tarih = params["tarih"]

        hatir_mesaj = params.get("aciklama", None)

        q_hatir_time = None
        if isinstance(hatir_time, datetime.time):
            q_hatir_time = QTime(hatir_time.hour, hatir_time.minute, hatir_time.second)

        yeni_hatirlatici = Hatirlatici(
            id=self.hatirlatici_id_sayaci,
            tarih=hatir_date,
            saat=q_hatir_time,
            yapildi=False,
            not_metni=f"NLP: {hatir_mesaj}",
            tekrarlama_tipi=tekrar_tipi,
            tekrarlama_araligi=params.get("tekrarlama_araligi", 0),
            son_tekrar_tarihi=None
        )

        self.hatirlaticilar.append(yeni_hatirlatici)
        self.hatirlatici_manager.hatirlatici_listelerini_guncelle()
        self.ayarlari_kaydet()

        show_toast(self, 'Yeni hatırlatıcı oluşturuldu', f"{aciklama}", 15000)
        self.natural_input.clear()

    def hatirlatici_duzenle(self, index):
        """Eski metod - artık kullanılmıyor, uyumluluk için bırakıldı"""
        if 0 <= index < len(self.hatirlaticilar):
            hatirlatici = self.hatirlaticilar[index]
            self.hatirlatici_manager.hatirlatici_duzenle_by_object(hatirlatici)

    def hatirlatici_sil(self, index):
        """Eski metod - artık kullanılmıyor, uyumluluk için bırakıldı"""
        if 0 <= index < len(self.hatirlaticilar):
            hatirlatici = self.hatirlaticilar[index]
            self.hatirlatici_manager.hatirlatici_sil_by_object(hatirlatici)

    def gecmis_sag_tik_menu(self, position):
        """Geçmiş listesi için sağ tık menüsü"""
        item = self.gecmis_listesi_widget.itemAt(position)
        if item:
            menu = QMenu()
            favori_ekle_action = menu.addAction("Favorilere Ekle")
            action = menu.exec_(self.gecmis_listesi_widget.mapToGlobal(position))

            if action == favori_ekle_action:
                self.favoriye_ekle(self.gecmis_listesi_widget.row(item))

    def favori_sag_tik_menu(self, position):
        """Favori listesi için sağ tık menüsü"""
        item = self.favori_listesi_widget.itemAt(position)
        menu = QMenu()
        favori_duzenle_action = None
        favoriden_sil_action = None

        if item:
            favori_duzenle_action = menu.addAction("Favoriyi Düzenle")
            favoriden_sil_action = menu.addAction("Favorilerden Sil")
            menu.addSeparator()

        yedekle_action = menu.addAction("Yedekle")
        geri_don_action = menu.addAction("Yedekten Geri Dön")

        action = menu.exec_(self.favori_listesi_widget.mapToGlobal(position))

        if item and action == favori_duzenle_action:
            self.favori_duzenle(self.favori_listesi_widget.row(item))
        elif item and action == favoriden_sil_action:
            self.favoriden_sil(self.favori_listesi_widget.row(item))
        elif action == yedekle_action:
            self.favori_yedekle()
        elif action == geri_don_action:
            self.favori_yedekten_geri_don()

    def favori_duzenle(self, favori_indeks):
        return self.helpers.favori_duzenle(favori_indeks)

    def favoriye_ekle(self, gecmis_indeks):
        return self.helpers.favoriye_ekle(gecmis_indeks)

    def favoriden_sil(self, favori_indeks):
        return self.helpers.favoriden_sil(favori_indeks)

    def favorileri_goster(self):
        return self.helpers.favorileri_goster()

    def favori_listesini_guncelle(self):
        return self.helpers.favori_listesini_guncelle()

    def favori_secimi_degisti(self):
        return self.helpers.favori_secimi_degisti()

    def secilen_favorileri_sil(self):
        return self.helpers.secilen_favorileri_sil()

    def favori_zamanlayici_baslat(self, item):
        item_text = item.text() if hasattr(item, 'text') else str(item)
        record_log(f"🚩 Favori zamanlayıcı başlatılıyor: {item_text}")
        yeni_z = self.helpers.favori_zamanlayici_baslat(item)

        if isinstance(item, dict):
            baslatilan_favori = item
        elif isinstance(item, int):
            baslatilan_favori = self.favori_listesi[item] if 0 <= item < len(self.favori_listesi) else None
        else:
            indeks = self.favori_listesi_widget.row(item)
            baslatilan_favori = self.favori_listesi[indeks] if 0 <= indeks < len(self.favori_listesi) else None

        if baslatilan_favori:
            self.bagli_favorileri_kontrol_et_ve_sor(baslatilan_favori)

        return yeni_z

    def bagli_favorileri_kontrol_et_ve_sor(self, baslatilan_favori, ziyaret_edilenler=None):
        """
        Başlatılan bir favori zamanlayıcıya 'Sonra Başlat' ile bağlı olan diğer favorileri kontrol eder ve kullanıcıya sorar.

        baslatilan_favori: Başlatılan favori verisi sözlüğü.
        ziyaret_edilenler: Döngüsel bağımlılıkları önlemek için ziyaret edilen favori isimleri kümesi.
        """
        if ziyaret_edilenler is None:
            ziyaret_edilenler = set()

        ana_aciklama = (baslatilan_favori.get('aciklama') or '').strip()
        if not ana_aciklama:
            return

        ziyaret_edilenler.add(ana_aciklama.lower())

        for f in self.favori_listesi:
            if not f.get('sonra_baslat_aktif'):
                continue

            beklenen = (f.get('beklenen_favori') or '').strip().lower()
            if not beklenen:
                continue

            ana_lower = ana_aciklama.lower()
            if beklenen == ana_lower or beklenen in ana_lower or ana_lower in beklenen:
                f_aciklama = (f.get('aciklama') or 'Zamanlayıcı').strip()
                f_lower = f_aciklama.lower()

                if f_lower in ziyaret_edilenler:
                    continue

                zaten_aktif = any(
                    z.sonra_baslat_aktif and (z.temel_aciklama or '').strip().lower() == f_lower
                    for z in self.aktif_zamanlayicilar
                )
                if zaten_aktif:
                    continue

                cevap = QMessageBox.question(
                    self,
                    "Bağlı Favori Zamanlayıcı",
                    f"'{ana_aciklama}' tamamlandığında başlayacak şekilde ayarlanmış "
                    f"'{f_aciklama}' ({f.get('sure', 0)} dk) favori zamanlayıcısı bulundu.\n\n"
                    f"Bunu da otomatik olarak (bekleme modunda) çalıştırmak istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if cevap == QMessageBox.Yes:
                    ziyaret_edilenler.add(f_lower)
                    self.helpers.favori_zamanlayici_baslat(f)
                    record_log(f"🔗 Bağlı favori zamanlayıcı bekleme modunda başlatıldı: {f_aciklama}")
                    show_toast(self, 'Bağlı Zamanlayıcı', f"'{f_aciklama}' bekleme modunda başlatıldı", 9000)
                    self.bagli_favorileri_kontrol_et_ve_sor(f, ziyaret_edilenler)

    def gecmis_secimi_degisti(self):
        return self.helpers.gecmis_secimi_degisti()

    def secilen_gecmisi_sil(self):
        return self.helpers.secilen_gecmisi_sil()

    def gecmisi_goster(self):
        return self.helpers.gecmisi_goster()

    def gecmis_zamanlayici_baslat(self, item):
        return self.helpers.gecmis_zamanlayici_baslat(item)

    def yeni_zamanlayici_baslat(self):
        """Yeni zamanlayıcı oluşturma iletişim kutusunu açar ve başlatır."""
        dialog = YeniZamanlayiciDialog(self, self.alarm_dosyalari, self.son_sure, self.veri_klasoru)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.getValues()
            dakika_ayari_degeri = values['dakika']
            aciklama = values['aciklama']
            alarm_dosyasi = values['alarm']
            tekrar_sayisi = values['tekrar_sayisi']
            tekrar_araligi_dakika = values['tekrar_araligi_dakika']
            alarm_zamani_aktif = values['alarm_zamani_aktif']
            alarm_zamani_str = values['alarm_zamani']
            sonra_baslat_aktif = values.get('sonra_baslat_aktif', False)
            beklenen_favori = values.get('beklenen_favori')

            self.zamanlayici_id_sayaci += 1
            yeni_zamanlayici = Zamanlayici(
                id=self.zamanlayici_id_sayaci, 
                dakika_ayari=dakika_ayari_degeri, 
                temel_aciklama=aciklama,
                alarm=alarm_dosyasi,
                tekrar_toplam_sayi=tekrar_sayisi,
                tekrar_mevcut_calisma=1, 
                tekrar_araligi_dakika=tekrar_araligi_dakika,
                ozel_saat_aktif_ilk_calisma=alarm_zamani_aktif,
                ozel_saat_str=alarm_zamani_str,
                sonra_baslat_aktif=sonra_baslat_aktif,
                beklenen_favori_aciklama=beklenen_favori
            )
            yeni_zamanlayici.baslama_zamani_ilk_kurulum = datetime.datetime.now()
            record_log(f"🚩 Yeni zamanlayıcı başlatılıyor: {yeni_zamanlayici.temel_aciklama} - {dakika_ayari_degeri} dakika, alarm: {alarm_dosyasi}, tekrar: {tekrar_sayisi}, aralık: {tekrar_araligi_dakika} dakika, özel saat: {alarm_zamani_str if alarm_zamani_aktif else 'Hayır'}, sonra başlat: {beklenen_favori if sonra_baslat_aktif else 'Hayır'}")

            if sonra_baslat_aktif:
                yeni_zamanlayici.sure = dakika_ayari_degeri * 60
                yeni_zamanlayici.toplam_sure = dakika_ayari_degeri * 60
                yeni_zamanlayici.ozel_saat_aktif_ilk_calisma = False
            elif alarm_zamani_aktif and alarm_zamani_str:
                try:
                    alarm_saati_qtime = QTime.fromString(alarm_zamani_str, "HH:mm")
                    simdiki_datetime = datetime.datetime.now()

                    alarm_hedef_datetime = datetime.datetime(
                        simdiki_datetime.year, simdiki_datetime.month, simdiki_datetime.day,
                        alarm_saati_qtime.hour(), alarm_saati_qtime.minute()
                    )

                    if alarm_hedef_datetime < simdiki_datetime:
                        alarm_hedef_datetime += datetime.timedelta(days=1)

                    fark_saniye = int((alarm_hedef_datetime - simdiki_datetime).total_seconds())
                    if fark_saniye < 0:
                        fark_saniye = 0

                    yeni_zamanlayici.sure = fark_saniye
                    yeni_zamanlayici.toplam_sure = fark_saniye
                except Exception as e:
                    QMessageBox.warning(self, "Hata", f"Alarm zamanı ayarlanırken hata: {e}\nNormal dakika bazlı zamanlayıcı başlatılacak.")
                    yeni_zamanlayici.sure = dakika_ayari_degeri * 60
                    yeni_zamanlayici.toplam_sure = dakika_ayari_degeri * 60
                    yeni_zamanlayici.ozel_saat_aktif_ilk_calisma = False
            else:
                yeni_zamanlayici.sure = dakika_ayari_degeri * 60
                yeni_zamanlayici.toplam_sure = dakika_ayari_degeri * 60

            self.aktif_zamanlayicilar.append(yeni_zamanlayici)
            self.zamanlayici_widget_olustur(yeni_zamanlayici)

            self.son_sure = dakika_ayari_degeri
            self.ayarlari_kaydet()
            show_toast(self, 'Yeni zamanlayıcı başlıtıldı', f"{yeni_zamanlayici.get_gorunen_aciklama()}", 15000)

    def zamanlayici_beklet_devam(self, zamanlayici_id):
        """Zamanlayıcıyı bekletir veya devam ettirir"""
        for zamanlayici in self.aktif_zamanlayicilar:
            if zamanlayici.id == zamanlayici_id:
                zamanlayici.calisma_durumu = not zamanlayici.calisma_durumu

                cerceve = self.findChild(QFrame, f"zamanlayici_{zamanlayici_id}")
                if cerceve:
                    beklet_dugme = cerceve.findChild(QPushButton, f"beklet_{zamanlayici_id}")
                    durum_ikonu = cerceve.findChild(QLabel, f"durum_ikonu_{zamanlayici_id}")

                    if zamanlayici.calisma_durumu:
                        if beklet_dugme:
                            beklet_dugme.setText("⏸️ Beklet")
                            beklet_dugme.setStyleSheet("background-color: #fff3cd;")
                        if durum_ikonu:
                            durum_ikonu.setText("▶️")
                            durum_ikonu.setToolTip("Aktif zamanlayıcı")
                        cerceve.setStyleSheet("")
                        record_log(f"▶️ Zamanlayıcı '{zamanlayici.temel_aciklama}' devam ediyor")
                        show_toast(self, 'Zamanlayıcı', f"{zamanlayici.temel_aciklama} devam ediyor", 3000)
                    else:
                        if beklet_dugme:
                            beklet_dugme.setText("▶️ Devam Et")
                            beklet_dugme.setStyleSheet("background-color: #c8e6c9;")
                        if durum_ikonu:
                            durum_ikonu.setText("⏸️")
                            durum_ikonu.setToolTip("Zamanlayıcı bekletildi")
                        # cerceve.setStyleSheet("background-color: #e3f2fd; border: 1px solid #2196f3; border-radius: 4px;")
                        cerceve.setStyleSheet(f"""
                            #zamanlayici_{zamanlayici_id} {{
                                background-color: #e3f2fd;
                                border: 1px solid #2196f3;
                                border-radius: 4px;
                            }}
                            QLabel {{
                                border: none;
                            }}
                        """)
                        record_log(f"⏸️ Zamanlayıcı '{zamanlayici.temel_aciklama}' bekletildi")
                        show_toast(self, 'Zamanlayıcı', f"{zamanlayici.temel_aciklama} bekletildi", 3000)

                self.ayarlari_kaydet()
                break

    def zamanlayici_durdur(self, zamanlayici_id):
        """Zamanlayıcıyı durdurur ve listeden kaldırır."""
        for i, zamanlayici in enumerate(self.aktif_zamanlayicilar):
            if zamanlayici.id == zamanlayici_id:
                self.aktif_zamanlayicilar.pop(i)
                record_log(f"❗❗❗Zamanlayıcı {zamanlayici.id} - '{zamanlayici.temel_aciklama}' durduruldu ve listeden kaldırıldı.", 'warning')

                cerceve = self.findChild(QFrame, f"zamanlayici_{zamanlayici_id}")
                if cerceve:
                    self.aktif_zamanlayicilar_alan.removeWidget(cerceve)
                    cerceve.deleteLater()

                self.ayarlari_kaydet()
                break

    def zamanlayici_tamamlandi(self, zamanlayici_id):
        """Zamanlayıcıyı tamamlandı olarak işaretler."""
        for i, zamanlayici in enumerate(self.aktif_zamanlayicilar):
            if zamanlayici.id == zamanlayici_id:
                erken_saniye = zamanlayici.sure
                erken_dakika = erken_saniye // 60
                erken_saniye_mod = erken_saniye % 60
                record_log(
                    f"✅ Zamanlayıcı '{zamanlayici.temel_aciklama}', {erken_dakika} dakika {erken_saniye_mod} saniye erken tamamlandı."
                )
                zamanlayici.sure = 1

    def zamanlayici_guncelle(self):
        """Her saniye zamanlayıcıları ve saat göstergesini günceller."""
        simdiki_zaman = QTime.currentTime()
        saat_metni = simdiki_zaman.toString("hh:mm:ss")
        self.saat_label.setText(saat_metni)

        for kronometre in self.aktif_kronometreler:
            if kronometre.calisma_durumu:
                kronometre.gecen_sure += 1

                cerceve = self.findChild(QFrame, f"kronometre_{kronometre.id}")
                if cerceve:
                    sure_label = cerceve.findChild(QLabel, f"krono_sure_{kronometre.id}")
                    if sure_label:
                        sure_label.setText(kronometre.get_formatted_time())

        ayarlar_degisti = False
        tamamlanan_zamanlayicilar = []

        for zamanlayici in self.aktif_zamanlayicilar[:]:
            if zamanlayici.sonra_baslat_aktif:
                sure_etiketi = self.findChild(QLabel, f"sure_{zamanlayici.id}")
                if sure_etiketi:
                    sure_metni = f"⏳ {format_time(zamanlayici.sure)}"
                    sure_etiketi.setText(sure_metni)
                continue

            if zamanlayici.calisma_durumu:
                zamanlayici.sure -= 1

                sure_etiketi = self.findChild(QLabel, f"sure_{zamanlayici.id}")
                if sure_etiketi:
                    sure_metni = format_time(zamanlayici.sure)
                    if zamanlayici.bekleme_modunda:
                        sure_metni = f"⏸ {sure_metni}"
                    sure_etiketi.setText(sure_metni)

                if zamanlayici.sure <= 0:
                    if zamanlayici.bekleme_modunda:
                        self.sonraki_tekrari_baslat(zamanlayici)
                        ayarlar_degisti = True
                    else:
                        tamamlanan_zamanlayicilar.append(zamanlayici)
                        ayarlar_degisti = True

        for zamanlayici in tamamlanan_zamanlayicilar:
            cerceve = self.findChild(QFrame, f"zamanlayici_{zamanlayici.id}")
            if cerceve:
                self.aktif_zamanlayicilar_alan.removeWidget(cerceve)
                cerceve.deleteLater()

            simdi = datetime.datetime.now()
            self.gecmis_listesi.append({
                'tarih': simdi.strftime('%d.%m.%Y %H:%M:%S'),
                'sure': zamanlayici.dakika_ayari,
                'aciklama': zamanlayici.temel_aciklama,
                'alarm': zamanlayici.alarm_dosyasi,
                'tekrar_toplam_sayi': zamanlayici.tekrar_toplam_sayi,
                'tekrar_mevcut_calisma': zamanlayici.tekrar_mevcut_calisma,
                'tekrar_araligi_dakika': zamanlayici.tekrar_araligi_dakika,
                'ozel_saat_aktif_ilk_calisma': zamanlayici.ozel_saat_aktif_ilk_calisma,
                'ozel_saat_str': zamanlayici.ozel_saat_str
            })
            self.helpers.gecmisi_goster(force_refresh_only_if_visible=True)

            record_log(f"🎉 Zamanlayıcı {zamanlayici.id} - '{zamanlayici.temel_aciklama}' ({zamanlayici.tekrar_mevcut_calisma} / {zamanlayici.tekrar_toplam_sayi}) tamamlandı")
            self.alarm_cal(zamanlayici.get_gorunen_aciklama(), zamanlayici.alarm_dosyasi)

            if zamanlayici.tekrar_mevcut_calisma < zamanlayici.tekrar_toplam_sayi:
                tekrar_zamanı_str = "şimdi" if zamanlayici.tekrar_araligi_dakika == 0 else f"{zamanlayici.tekrar_araligi_dakika} dakika sonra"
                record_log(f"🔁 {get_current_datetime_string()} Zamanlayıcı {zamanlayici.id} - '{zamanlayici.temel_aciklama}' {tekrar_zamanı_str} tekrar başlatılacak...")
                self.bekleme_zamanlayicisi_olustur(zamanlayici)
            else:
                self.sonra_baslat_tetikle(zamanlayici)

            try:
                self.aktif_zamanlayicilar.remove(zamanlayici)
            except ValueError:
                pass

        if hasattr(self, '_son_liste_guncelleme'):
            gecen_sure = (datetime.datetime.now() - self._son_liste_guncelleme).total_seconds()
            if gecen_sure >= 30:
                self.hatirlatici_manager.hatirlatici_listelerini_guncelle(kalan_sure_guncelle=True)
                self._son_liste_guncelleme = datetime.datetime.now()
        else:
            self._son_liste_guncelleme = datetime.datetime.now()

        record_log("🔍 [HATIRLATICI] Hatırlatıcı kontrol döngüsü başlıyor", "debug")
        self.hatirlatici_manager.hatirlatici_kontrol()

        if ayarlar_degisti:
            self.ayarlari_kaydet()

    def sonra_baslat_tetikle(self, tamamlanan_zamanlayici):
        """Bir zamanlayıcının tüm tekrarları bittiğinde, onu bekleyen zamanlayıcıları başlatır."""
        tamamlanan_ad = tamamlanan_zamanlayici.temel_aciklama.strip().lower()
        for z in self.aktif_zamanlayicilar:
            if z.sonra_baslat_aktif and z.beklenen_favori_aciklama:
                beklenen = z.beklenen_favori_aciklama.strip().lower()
                if beklenen == tamamlanan_ad or beklenen in tamamlanan_ad or tamamlanan_ad in beklenen:
                    z.sonra_baslat_aktif = False
                    z.calisma_durumu = True
                    record_log(f"🚀 Bekleyen zamanlayıcı başlatıldı: {z.id} - '{z.temel_aciklama}' (Beklenen '{tamamlanan_zamanlayici.temel_aciklama}' tamamlandı)")
                    self.guncelle_zamanlayici_widget_arayuzu(z)

    def bekleme_zamanlayicisi_olustur(self, onceki_zamanlayici):
        """Tekrar aralığı için bekleme zamanlayıcısı oluşturur."""
        self.zamanlayici_id_sayaci += 1
        yeni_tekrar_no = onceki_zamanlayici.tekrar_mevcut_calisma + 1

        bekleme_zamanlayici = Zamanlayici(
            id=self.zamanlayici_id_sayaci,
            dakika_ayari=onceki_zamanlayici.dakika_ayari,
            temel_aciklama=onceki_zamanlayici.temel_aciklama,
            alarm=onceki_zamanlayici.alarm_dosyasi,
            baslama_zamani_ilk_kurulum=onceki_zamanlayici.baslama_zamani_ilk_kurulum,
            tekrar_toplam_sayi=onceki_zamanlayici.tekrar_toplam_sayi,
            tekrar_mevcut_calisma=yeni_tekrar_no,
            tekrar_araligi_dakika=onceki_zamanlayici.tekrar_araligi_dakika,
            ozel_saat_aktif_ilk_calisma=False,
            ozel_saat_str=None
        )

        bekleme_zamanlayici.bekleme_modunda = True
        bekleme_suresi_saniye = onceki_zamanlayici.tekrar_araligi_dakika * 60

        if bekleme_suresi_saniye == 0:
            bekleme_zamanlayici.bekleme_modunda = False
            bekleme_zamanlayici.sure = onceki_zamanlayici.dakika_ayari * 60
            bekleme_zamanlayici.toplam_sure = onceki_zamanlayici.dakika_ayari * 60
        else:
            bekleme_zamanlayici.sure = bekleme_suresi_saniye
            bekleme_zamanlayici.toplam_sure = bekleme_suresi_saniye

        self.aktif_zamanlayicilar.append(bekleme_zamanlayici)
        self.zamanlayici_widget_olustur(bekleme_zamanlayici)
        self.ayarlari_kaydet()

    def sonraki_tekrari_baslat(self, onceki_zamanlayici_bilgileri):
        """Bekleme süresi dolduktan sonra asıl zamanlayıcıyı başlatır."""
        record_log(f"🔁 {get_current_datetime_string()}: '{onceki_zamanlayici_bilgileri.id} -{onceki_zamanlayici_bilgileri.temel_aciklama}' tekrar başlatıldı")

        tekrar_araligi_str = "(Beklemeden tekrar)" if onceki_zamanlayici_bilgileri.tekrar_araligi_dakika == 0 else f"{onceki_zamanlayici_bilgileri.tekrar_araligi_dakika} dakika"
        record_log(f"   🔸Tekrar Aralığı      : {tekrar_araligi_str}")
        record_log(f"   🔸Mevcut Tekrar #     : {onceki_zamanlayici_bilgileri.tekrar_mevcut_calisma}")
        record_log(f"   🔸Toplam Tekrar Sayısı: {onceki_zamanlayici_bilgileri.tekrar_toplam_sayi}")

        onceki_zamanlayici_bilgileri.bekleme_modunda = False
        onceki_zamanlayici_bilgileri.sure = onceki_zamanlayici_bilgileri.dakika_ayari * 60
        onceki_zamanlayici_bilgileri.toplam_sure = onceki_zamanlayici_bilgileri.dakika_ayari * 60

        self.guncelle_zamanlayici_widget_arayuzu(onceki_zamanlayici_bilgileri)
        self.ayarlari_kaydet()

    def alarm_cal(self, aciklama, alarm_dosyasi=VARSAYILAN_ALARM_DOSYASI):
        """Alarmı çal ve bildirim göster (çoklu ses seçilmişse rastgele birini çalar)"""
        coklu_secim = isinstance(alarm_dosyasi, list) and len(alarm_dosyasi) > 1
        if isinstance(alarm_dosyasi, list):
            secenekler = [a for a in alarm_dosyasi if a]
            secilen_dosya = random.choice(secenekler) if secenekler else VARSAYILAN_ALARM_DOSYASI
        else:
            secilen_dosya = alarm_dosyasi or VARSAYILAN_ALARM_DOSYASI

        alarm_bilgi_metni = f"{secilen_dosya} (🎲 {len(alarm_dosyasi)} ses arasından)" if coklu_secim else secilen_dosya
        mesaj = f"Zamanlayıcı süresi doldu!\nAçıklama: {aciklama}\nAlarm: {alarm_bilgi_metni}"
        dosya_yolu = os.path.join(self.veri_klasoru, secilen_dosya)

        gosterim_zamani = datetime.datetime.now()

        if not os.path.exists(dosya_yolu):
            dosya_yolu = os.path.join(self.veri_klasoru, VARSAYILAN_ALARM_DOSYASI)
            secilen_dosya = VARSAYILAN_ALARM_DOSYASI
            if not os.path.exists(dosya_yolu):
                QMessageBox.warning(self, "Hata", f"Alarm dosyası bulunamadı: {secilen_dosya}")
                return

        dialog = AlarmDialog(self, "Süre Doldu", mesaj, dosya_yolu)
        record_log(f"🎵 ({aciklama}) Alarm çalınıyor: {alarm_bilgi_metni}")
        dialog.exec_()

        gecen_sure = datetime.datetime.now() - gosterim_zamani
        gecen_saniye = gecen_sure.total_seconds()

        for zamanlayici in self.aktif_zamanlayicilar:
            if zamanlayici.calisma_durumu:
                zamanlayici.sure -= int(gecen_saniye)
                if zamanlayici.sure < 0:
                    zamanlayici.sure = 0


if __name__ == "__main__":
    print("Veri Klasörü: ", VERI_KLASORU)
    print("Log Dosyası: ", LOG_DOSYASI)

    setup_logging(LOG_DOSYASI)
    app = QApplication(sys.argv)
    pencere = AnaUygulamaPenceresi()
    pencere.show()
    sys.exit(app.exec_())
