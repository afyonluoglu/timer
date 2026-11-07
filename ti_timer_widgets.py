"""
Aktif zamanlayıcı kartlarının oluşturulması, düzenlenmesi ve arayüz güncellemelerini yöneten Mixin modülü.
"""

import datetime
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QInputDialog, QDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTime

from dialog_classes import ClickableFrame, YeniZamanlayiciDialog
from timer_logger import record_log


class TimerWidgetsMixin:
    """Zamanlayıcı widget kartları ve düzenleme diyaloglarını yöneten Mixin sınıfı."""

    def zamanlayici_widget_olustur(self, zamanlayici):
        """Zamanlayıcı için görsel kart widget'ı oluşturur"""
        zamanlayici_cerceve = ClickableFrame(f"zamanlayici_{zamanlayici.id}")
        zamanlayici_cerceve.setObjectName(f"zamanlayici_{zamanlayici.id}")
        zamanlayici_cerceve.setMaximumHeight(45) 
        zamanlayici_cerceve.setFrameStyle(QFrame.Box | QFrame.Raised)
        zamanlayici_cerceve.setLineWidth(1)
        zamanlayici_cerceve.doubleClicked.connect(self.handle_timer_double_click_event)
        zamanlayici_cerceve.setFixedHeight(55)  # Her alarm satırının yüksekliği


        if zamanlayici.bekleme_modunda or zamanlayici.sonra_baslat_aktif:
            # zamanlayici_cerceve.setStyleSheet("background-color: #fff3cd; border: 2px solid #ffc107;")
            zamanlayici_cerceve.setStyleSheet(f"""
                #zamanlayici_{zamanlayici.id} {{
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 4px;
                }}
                QLabel {{
                    border: none;
                }}
            """)

        zamanlayici_duzen = QHBoxLayout()
        # Sol, Üst, Sağ, Alt boşluklar (dikey boşluklar 2 piksele düşürülür):
        zamanlayici_duzen.setContentsMargins(6, 2, 6, 2)
        zamanlayici_duzen.setSpacing(6)

        durum_ikonu = QLabel()
        if zamanlayici.sonra_baslat_aktif:
            durum_ikonu.setText("⏳")
            durum_ikonu.setStyleSheet("font-size: 18px; border: none;")
            durum_ikonu.setToolTip(f"{zamanlayici.beklenen_favori_aciklama} zamanlayıcısı bekleniyor")
        elif zamanlayici.bekleme_modunda:
            durum_ikonu.setText("⏳")
            durum_ikonu.setStyleSheet("font-size: 18px; border: none;")
            durum_ikonu.setToolTip("Sonraki tekrar için bekleniyor")
        else:
            durum_ikonu.setText("▶️")
            durum_ikonu.setStyleSheet("font-size: 18px; border: none;")
            durum_ikonu.setToolTip("Aktif zamanlayıcı")
        durum_ikonu.setObjectName(f"durum_ikonu_{zamanlayici.id}")
        zamanlayici_duzen.addWidget(durum_ikonu)

        aciklama_etiketi = QLabel(zamanlayici.get_gorunen_aciklama())
        aciklama_etiketi.setMinimumWidth(150)
        aciklama_etiketi.setObjectName(f"aciklama_{zamanlayici.id}")
        zamanlayici_duzen.addWidget(aciklama_etiketi)

        sure_metni = f"{zamanlayici.sure // 60:02d}:{zamanlayici.sure % 60:02d}"
        if zamanlayici.sonra_baslat_aktif:
            sure_metni = f"⏳ {sure_metni}"
        elif zamanlayici.bekleme_modunda:
            sure_metni = f"⏸ {sure_metni}"

        kalan_sure_etiketi = QLabel(sure_metni)
        kalan_sure_etiketi.setObjectName(f"sure_{zamanlayici.id}")
        kalan_sure_etiketi.setAlignment(Qt.AlignCenter)
        kalan_sure_etiketi.setFont(QFont("Arial", 12, QFont.Bold))
        if zamanlayici.bekleme_modunda or zamanlayici.sonra_baslat_aktif:
            kalan_sure_etiketi.setStyleSheet("color: #856404;")
        zamanlayici_duzen.addWidget(kalan_sure_etiketi)

        toplam_sure_etiketi = QLabel(f"/{zamanlayici.toplam_sure // 60:02d}:{zamanlayici.toplam_sure % 60:02d}")
        toplam_sure_etiketi.setObjectName(f"toplam_sure_{zamanlayici.id}")
        zamanlayici_duzen.addWidget(toplam_sure_etiketi)

        if zamanlayici.varsayilan_disi_alarm_var_mi():
            alarm_etiketi = QLabel(zamanlayici.get_alarm_kisa_etiket())
            alarm_etiketi.setToolTip(zamanlayici.get_alarm_ipucu())
            alarm_etiketi.setObjectName(f"alarm_label_{zamanlayici.id}")
            zamanlayici_duzen.addWidget(alarm_etiketi)

        self.complete_button = QPushButton("✅ Tamamlandı")
        self.complete_button.setStyleSheet("background-color: #d1fdb6;")
        self.complete_button.setObjectName(f"tamamlandi_{zamanlayici.id}")
        self.complete_button.clicked.connect(lambda checked, z_id=zamanlayici.id: self.zamanlayici_tamamlandi(z_id)) 
        zamanlayici_duzen.addWidget(self.complete_button)

        self.setTime_button = QPushButton("⏱️ Süre Ayarla")
        self.setTime_button.setStyleSheet("background-color: #b6ddfd;")
        self.setTime_button.setObjectName(f"SetTime_{zamanlayici.id}")
        self.setTime_button.clicked.connect(lambda checked, z_id=zamanlayici.id: self.süre_Degistir(z_id))
        zamanlayici_duzen.addWidget(self.setTime_button)

        if zamanlayici.calisma_durumu:
            beklet_dugme = QPushButton("⏸️ Beklet")
            beklet_dugme.setStyleSheet("background-color: #fff3cd;")
        else:
            beklet_dugme = QPushButton("▶️ Devam Et")
            beklet_dugme.setStyleSheet("background-color: #c8e6c9;")
        beklet_dugme.setObjectName(f"beklet_{zamanlayici.id}")
        beklet_dugme.clicked.connect(lambda checked, z_id=zamanlayici.id: self.zamanlayici_beklet_devam(z_id))
        zamanlayici_duzen.addWidget(beklet_dugme)

        durdur_dugme = QPushButton("❌ Durdur")
        durdur_dugme.setObjectName(f"durdur_{zamanlayici.id}")
        durdur_dugme.setStyleSheet("background-color: #ffcdd2;")
        durdur_dugme.clicked.connect(lambda checked, z_id=zamanlayici.id: self.zamanlayici_durdur(z_id))
        zamanlayici_duzen.addWidget(durdur_dugme)

        zamanlayici_cerceve.setLayout(zamanlayici_duzen)
        self.aktif_zamanlayicilar_alan.addWidget(zamanlayici_cerceve)

    def handle_timer_double_click_event(self, timer_object_name_str):
        """Çift tıklanan zamanlayıcı için düzenleme diyalogunu açar."""
        try:
            timer_id = int(timer_object_name_str.split('_')[-1])
            self.duzenle_aktif_zamanlayici(timer_id)
        except (IndexError, ValueError) as e:
            record_log(f"Hata: Zamanlayıcı ID'si ayrıştırılamadı: {timer_object_name_str}, {e}", "error")

    def duzenle_aktif_zamanlayici(self, timer_id):
        """Aktif bir zamanlayıcıyı düzenleme iletişim kutusunu açar."""
        target_timer = None
        for t in self.aktif_zamanlayicilar:
            if t.id == timer_id:
                target_timer = t
                break

        if not target_timer:
            QMessageBox.warning(self, "Hata", "Düzenlenecek zamanlayıcı bulunamadı.")
            return

        dialog = YeniZamanlayiciDialog(self, self.alarm_dosyalari,
                                       varsayilan_sure=target_timer.dakika_ayari,
                                       veri_klasoru=self.veri_klasoru,
                                       zamanlayici_to_edit=target_timer)

        if dialog.exec_() == QDialog.Accepted:
            values = dialog.getValues()

            target_timer.temel_aciklama = values['aciklama']
            target_timer.alarm_dosyasi = values['alarm']
            target_timer.tekrar_toplam_sayi = values['tekrar_sayisi']
            target_timer.tekrar_araligi_dakika = values['tekrar_araligi_dakika']

            new_dakika_ayari = values['dakika']
            new_ozel_saat_aktif = values['alarm_zamani_aktif']
            new_ozel_saat_str = values['alarm_zamani']
            new_sonra_baslat_aktif = values.get('sonra_baslat_aktif', False)
            new_beklenen_favori = values.get('beklenen_favori')

            timing_changed = False
            if new_ozel_saat_aktif != target_timer.ozel_saat_aktif_ilk_calisma or \
               (new_ozel_saat_aktif and new_ozel_saat_str != target_timer.ozel_saat_str) or \
               (not new_ozel_saat_aktif and new_dakika_ayari != target_timer.dakika_ayari) or \
               (new_sonra_baslat_aktif != target_timer.sonra_baslat_aktif) or \
               (new_beklenen_favori != target_timer.beklenen_favori_aciklama):
                timing_changed = True

            target_timer.dakika_ayari = new_dakika_ayari
            target_timer.ozel_saat_aktif_ilk_calisma = new_ozel_saat_aktif
            target_timer.ozel_saat_str = new_ozel_saat_str if new_ozel_saat_aktif else None
            target_timer.sonra_baslat_aktif = new_sonra_baslat_aktif
            target_timer.beklenen_favori_aciklama = new_beklenen_favori

            if timing_changed:
                if target_timer.sonra_baslat_aktif:
                    target_timer.ozel_saat_aktif_ilk_calisma = False
                    target_timer.sure = target_timer.dakika_ayari * 60
                    target_timer.toplam_sure = target_timer.dakika_ayari * 60
                elif target_timer.ozel_saat_aktif_ilk_calisma and target_timer.ozel_saat_str and target_timer.tekrar_mevcut_calisma == 1:
                    try:
                        alarm_saati_qtime = QTime.fromString(target_timer.ozel_saat_str, "HH:mm")
                        simdiki_datetime = datetime.datetime.now()
                        alarm_hedef_datetime = datetime.datetime(
                            simdiki_datetime.year, simdiki_datetime.month, simdiki_datetime.day,
                            alarm_saati_qtime.hour(), alarm_saati_qtime.minute()
                        )
                        if alarm_hedef_datetime < simdiki_datetime:
                            alarm_hedef_datetime += datetime.timedelta(days=1)

                        fark_saniye = int((alarm_hedef_datetime - simdiki_datetime).total_seconds())
                        target_timer.sure = max(0, fark_saniye)
                        target_timer.toplam_sure = max(0, fark_saniye)
                    except Exception as e:
                        QMessageBox.warning(self, "Hata", f"Alarm zamanı güncellenirken hata: {e}. Süreye dayalıya dönülüyor.")
                        target_timer.ozel_saat_aktif_ilk_calisma = False
                        target_timer.sure = target_timer.dakika_ayari * 60
                        target_timer.toplam_sure = target_timer.dakika_ayari * 60
                else:
                    target_timer.ozel_saat_aktif_ilk_calisma = False 
                    target_timer.sure = target_timer.dakika_ayari * 60
                    target_timer.toplam_sure = target_timer.dakika_ayari * 60

            self.guncelle_zamanlayici_widget_arayuzu(target_timer)
            self.ayarlari_kaydet()

    def guncelle_zamanlayici_widget_arayuzu(self, zamanlayici):
        """Belirli bir zamanlayıcının arayüzdeki widget'larını günceller."""
        cerceve = self.findChild(ClickableFrame, f"zamanlayici_{zamanlayici.id}")
        if not cerceve:
            return

        if zamanlayici.bekleme_modunda or zamanlayici.sonra_baslat_aktif:
            cerceve.setStyleSheet("background-color: #fff3cd; border: 2px solid #ffc107;")
        else:
            cerceve.setStyleSheet("")

        durum_ikonu = cerceve.findChild(QLabel, f"durum_ikonu_{zamanlayici.id}")
        if durum_ikonu:
            if zamanlayici.sonra_baslat_aktif:
                durum_ikonu.setText("⏳")
                durum_ikonu.setToolTip(f"{zamanlayici.beklenen_favori_aciklama} zamanlayıcısı bekleniyor")
            elif zamanlayici.bekleme_modunda:
                durum_ikonu.setText("⏳")
                durum_ikonu.setToolTip("Sonraki tekrar için bekleniyor")
            else:
                durum_ikonu.setText("▶️")
                durum_ikonu.setToolTip("Aktif zamanlayıcı")

        aciklama_etiketi = cerceve.findChild(QLabel, f"aciklama_{zamanlayici.id}")
        if aciklama_etiketi:
            aciklama_etiketi.setText(zamanlayici.get_gorunen_aciklama())

        kalan_sure_etiketi = cerceve.findChild(QLabel, f"sure_{zamanlayici.id}")
        if kalan_sure_etiketi:
            sure_metni = f"{zamanlayici.sure // 60:02d}:{zamanlayici.sure % 60:02d}"
            if zamanlayici.sonra_baslat_aktif:
                sure_metni = f"⏳ {sure_metni}"
                kalan_sure_etiketi.setStyleSheet("color: #856404;")
            elif zamanlayici.bekleme_modunda:
                sure_metni = f"⏸ {sure_metni}"
                kalan_sure_etiketi.setStyleSheet("color: #856404;")
            else:
                kalan_sure_etiketi.setStyleSheet("")
            kalan_sure_etiketi.setText(sure_metni)

        toplam_sure_etiketi = cerceve.findChild(QLabel, f"toplam_sure_{zamanlayici.id}")
        if toplam_sure_etiketi:
            toplam_sure_etiketi.setText(f"/{zamanlayici.toplam_sure // 60:02d}:{zamanlayici.toplam_sure % 60:02d}")

        layout = cerceve.layout()
        alarm_label_widget = cerceve.findChild(QLabel, f"alarm_label_{zamanlayici.id}")
        should_have_alarm_label = zamanlayici.varsayilan_disi_alarm_var_mi()

        if should_have_alarm_label:
            new_alarm_text = zamanlayici.get_alarm_kisa_etiket()
            new_tooltip = zamanlayici.get_alarm_ipucu()
            if alarm_label_widget:
                alarm_label_widget.setText(new_alarm_text)
                alarm_label_widget.setToolTip(new_tooltip)
                alarm_label_widget.setVisible(True)
            else:
                durdur_dugme = cerceve.findChild(QPushButton, f"durdur_{zamanlayici.id}")
                if durdur_dugme and layout:
                    idx = layout.indexOf(durdur_dugme)
                    if idx != -1:
                        new_alarm_label = QLabel(new_alarm_text)
                        new_alarm_label.setToolTip(new_tooltip)
                        new_alarm_label.setObjectName(f"alarm_label_{zamanlayici.id}")
                        layout.insertWidget(idx, new_alarm_label)
        elif alarm_label_widget:
            if layout:
                layout.removeWidget(alarm_label_widget)
            alarm_label_widget.deleteLater()

    def süre_Degistir(self, zamanlayici_id):
        """Zamanlayıcının süresini kullanıcıdan alınan değerle değiştirir."""
        for i, zamanlayici in enumerate(self.aktif_zamanlayicilar):
            if zamanlayici.id == zamanlayici_id:
                bilgi = self.kullanicidan_sayi_al()
                if bilgi is not None:
                    record_log(f"💫 Zamanalyıcı süresi değiştirildi: {zamanlayici.id} - '{zamanlayici.temel_aciklama}' - Yeni süre: {bilgi} dakika")
                    zamanlayici.sure = bilgi * 60

    def kullanicidan_sayi_al(self):
        """Kullanıcıdan dakika olarak yeni süre girmesini ister."""
        girilen_sayi, ok = QInputDialog.getInt(self, 
                                               "Süre Girişi", 
                                               "Dakika olarak (0-120 arası) yeni süre:", 
                                               value=10,
                                               min=0,
                                               max=120,
                                               step=1)
        if ok:
            return girilen_sayi
        else:
            return None

