# dialog_classes.py
import sys
import os
import json
import random
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                           QSpinBox, QLineEdit, QCheckBox, QTimeEdit, QComboBox, 
                           QPushButton, QLabel, QMessageBox, QProgressBar, QFrame,
                           QScrollArea, QApplication, QTextEdit)  
from PyQt5.QtCore import Qt, QTime, QUrl, QTimer, QEvent
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import re

# Modül ayrımı: Taşınan diyalog sınıfları ti_dialogs modülünden içe aktarılır
from ti_dialogs import IlerlemeDialog, YardimPenceresi, AlarmDialog
from ti_models import VARSAYILAN_ALARM_DOSYASI


class CheckableComboBox(QComboBox):
    """Birden fazla öğenin checkbox ile işaretlenebildiği özel ComboBox sınıfı"""
    secimDegisti = pyqtSignal()

    def __init__(self, parent=None):
        """Çoklu seçimli ComboBox bileşenini başlatır"""
        super().__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().installEventFilter(self)
        self.view().viewport().installEventFilter(self)
        self._son_tiklanan_veri = None
        self.model().dataChanged.connect(self._veri_degisti)

    def eventFilter(self, obj, event):
        """Fare tıklamalarını yakalayarak öğelerin işaretlenmesini ve menünün açık kalmasını sağlar"""
        if obj == self.lineEdit() and event.type() == QEvent.MouseButtonRelease:
            if self.view().isVisible():
                self.hidePopup()
            else:
                self.showPopup()
            return True

        if obj == self.view().viewport() and event.type() == QEvent.MouseButtonRelease:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                item = self.model().itemFromIndex(index)
                yeni_durum = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                item.setCheckState(yeni_durum)
                self._son_tiklanan_veri = item.data(Qt.UserRole)
                self.metni_guncelle()
                self.secimDegisti.emit()
                return True
        return super().eventFilter(obj, event)

    def _veri_degisti(self, top_left, bottom_right, roles=None):
        """Model verisi değiştiğinde görünen metni günceller"""
        self.metni_guncelle()
        self.secimDegisti.emit()

    def addCheckableItem(self, text, data=None, checked=False):
        """ComboBox içerisine işaretlenebilir yeni bir öğe ekler"""
        item = QStandardItem(text)
        item.setData(data if data is not None else text, Qt.UserRole)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        item.setData(Qt.Checked if checked else Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)
        self.metni_guncelle()

    def checkedDataList(self):
        """İşaretlenmiş olan tüm öğelerin veri (dosya adı) listesini döndürür"""
        secililer = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.Checked:
                secililer.append(item.data(Qt.UserRole))
        return secililer

    def setCheckedDataList(self, alarm_verisi):
        """Verilen tekil alarm adını veya alarm listesini ComboBox içinde işaretler"""
        if isinstance(alarm_verisi, list):
            hedef_kume = set(alarm_verisi)
        elif isinstance(alarm_verisi, str) and alarm_verisi:
            hedef_kume = {alarm_verisi}
        else:
            hedef_kume = {VARSAYILAN_ALARM_DOSYASI}

        self.model().blockSignals(True)
        herhangi_biri_secildi = False
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            veri = item.data(Qt.UserRole)
            if veri in hedef_kume:
                item.setCheckState(Qt.Checked)
                herhangi_biri_secildi = True
            else:
                item.setCheckState(Qt.Unchecked)

        if not herhangi_biri_secildi and self.model().rowCount() > 0:
            self.model().item(0).setCheckState(Qt.Checked)
        self.model().blockSignals(False)
        self.metni_guncelle()

    def metni_guncelle(self):
        """İşaretli öğelere göre ComboBox üzerindeki özet metni ve ipucunu günceller"""
        secili_metinler = []
        secili_veriler = []
        for i in range(self.model().rowCount()):
            item = self.model().item(i)
            if item.checkState() == Qt.Checked:
                secili_metinler.append(item.text())
                secili_veriler.append(str(item.data(Qt.UserRole)))

        if not secili_veriler:
            ozet = f"Varsayılan ({VARSAYILAN_ALARM_DOSYASI})"
            ipucu = f"Hiçbir ses işaretlenmediği için varsayılan ({VARSAYILAN_ALARM_DOSYASI}) çalınır"
        elif len(secili_veriler) == 1:
            ozet = secili_metinler[0]
            ipucu = f"Seçili ses: {secili_veriler[0]}"
        else:
            ozet = f"🎲 {len(secili_veriler)} ses seçili ({', '.join(secili_veriler)})"
            ipucu = "Rastgele çalınacak sesler:\n• " + "\n• ".join(secili_veriler)

        if self.lineEdit():
            self.lineEdit().setText(ozet)
        self.setToolTip(ipucu)


class ClickableFrame(QFrame):
    """Çift tıklanabilir frame sınıfı"""
    doubleClicked = pyqtSignal(str)  # Zamanlayıcı ID'sini (string olarak) taşıyacak sinyal

    def __init__(self, timer_id_str, parent=None):
        super().__init__(parent)
        self.timer_id_str = timer_id_str

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit(self.timer_id_str)
        super().mouseDoubleClickEvent(event)


class YeniZamanlayiciDialog(QDialog):
    """Yeni zamanlayıcı oluşturma ve düzenleme dialogu"""
    
    def __init__(self, parent=None, alarm_dosyalari=None, varsayilan_sure=5, veri_klasoru=None, zamanlayici_to_edit=None, is_editing_favorite=False):
        super().__init__(parent)
        
        self.is_editing_favorite = is_editing_favorite
        self.parent_app = parent
        if self.parent_app and hasattr(self.parent_app, 'alarm_dosyalarini_bul'):
            self.parent_app.alarm_dosyalarini_bul()
            self.alarm_dosyalari = self.parent_app.alarm_dosyalari
        else:
            self.alarm_dosyalari = alarm_dosyalari or []
        self.veri_klasoru = veri_klasoru
        self.editing_timer = zamanlayici_to_edit

        if self.editing_timer:
            if self.is_editing_favorite:
                self.setWindowTitle("Favoriyi Düzenle")
            else:
                self.setWindowTitle("Zamanlayıcıyı Düzenle")
        else:
            self.setWindowTitle("Yeni Zamanlayıcı")

        self.resize(420, 370)
        
        self.medya_oynatici = QMediaPlayer()
        self.medya_oynatici.stateChanged.connect(self.oynatici_durum_degisti)
        self.mevcut_calma_dosyasi = None
        
        self.arayuz_olustur()
        self.degerleri_doldur(varsayilan_sure)

    def arayuz_olustur(self):
        """Dialog arayüzünü oluştur"""
        form_duzen = QFormLayout()
        
        self.dakika_spinner = QSpinBox()
        self.dakika_spinner.setRange(1, 180)
        form_duzen.addRow("Dakika (Tekrarlar için):", self.dakika_spinner)
        
        self.aciklama_girisi = QLineEdit()
        self.aciklama_girisi.setPlaceholderText("Zamanlayıcı için açıklama giriniz")
        form_duzen.addRow("Açıklama:", self.aciklama_girisi)
        
        self.alarm_zamani_checkbox = QCheckBox("Alarm Zamanı Belirle (İlk Alarm İçin)")
        self.alarm_zamani_checkbox.stateChanged.connect(self.alarm_zamani_durumu_degisti)
        form_duzen.addRow(self.alarm_zamani_checkbox)

        self.alarm_zamani_edit = QTimeEdit()
        self.alarm_zamani_edit.setDisplayFormat("HH:mm")
        self.alarm_zamani_edit.setEnabled(False)
        form_duzen.addRow("Alarm Saati:", self.alarm_zamani_edit)

        # Sonra Başlat bileşenleri
        self.sonra_baslat_checkbox = QCheckBox("Sonra Başlat")
        self.sonra_baslat_checkbox.stateChanged.connect(self.sonra_baslat_durumu_degisti)
        form_duzen.addRow(self.sonra_baslat_checkbox)

        self.sonra_baslat_combobox = QComboBox()
        self.sonra_baslat_combobox.setEnabled(False)
        self.favorileri_comboboxa_yukle()
        form_duzen.addRow("Beklenecek Zamanlayıcı:", self.sonra_baslat_combobox)

        alarm_duzen = QHBoxLayout()
        self.alarm_secici = CheckableComboBox()
        self.alarm_secici.addCheckableItem(f"Varsayılan ({VARSAYILAN_ALARM_DOSYASI})", VARSAYILAN_ALARM_DOSYASI, checked=True)
        for dosya in self.alarm_dosyalari:
            if dosya != VARSAYILAN_ALARM_DOSYASI:
                self.alarm_secici.addCheckableItem(dosya, dosya, checked=False)
        self.alarm_secici.secimDegisti.connect(self.alarm_secimi_degisti)
        alarm_duzen.addWidget(self.alarm_secici)
        
        self.cal_durdur_dugme = QPushButton("Çal")
        self.cal_durdur_dugme.setFixedWidth(60)
        self.cal_durdur_dugme.clicked.connect(self.alarm_cal_durdur)
        alarm_duzen.addWidget(self.cal_durdur_dugme)
        form_duzen.addRow("Alarm Sesi:", alarm_duzen)

        self.tekrar_sayisi_spinner = QSpinBox()
        self.tekrar_sayisi_spinner.setRange(1, 99)
        self.tekrar_sayisi_spinner.setValue(1)
        self.tekrar_sayisi_spinner.valueChanged.connect(self.tekrar_ayarlarini_guncelle)
        form_duzen.addRow("Tekrar Sayısı:", self.tekrar_sayisi_spinner)

        self.tekrar_araligi_spinner = QSpinBox()
        self.tekrar_araligi_spinner.setRange(0, 180)
        self.tekrar_araligi_spinner.setValue(0)
        self.tekrar_araligi_spinner.setEnabled(False)
        form_duzen.addRow("Tekrar Aralığı (dk):", self.tekrar_araligi_spinner)
        
        buton_duzen = QHBoxLayout()

        # Favorilere Ekle düğmesi (sadece yeni zamanlayıcı modunda)
        if not self.editing_timer:
            self.favorilere_ekle_butonu = QPushButton("Favorilere Ekle")
            self.favorilere_ekle_butonu.clicked.connect(self.favorilere_ekle)
            buton_duzen.addWidget(self.favorilere_ekle_butonu)

        self.tamam_butonu = QPushButton("Tamam")
        self.tamam_butonu.clicked.connect(self.accept)
        buton_duzen.addWidget(self.tamam_butonu)
        
        self.iptal_butonu = QPushButton("İptal")
        self.iptal_butonu.clicked.connect(self.reject)
        buton_duzen.addWidget(self.iptal_butonu)
        form_duzen.addRow("", buton_duzen)
        
        self.setLayout(form_duzen)

    def favorileri_comboboxa_yukle(self):
        """Favori zamanlayıcıları combobox'a yükle"""
        self.sonra_baslat_combobox.clear()
        if self.parent_app and hasattr(self.parent_app, 'favori_listesi') and self.parent_app.favori_listesi:
            for favori in self.parent_app.favori_listesi:
                aciklama = favori.get('aciklama', 'Zamanlayıcı')
                sure = favori.get('sure', 0)
                gorunen_ad = f"⭐ {sure} dk - {aciklama}"
                self.sonra_baslat_combobox.addItem(gorunen_ad, aciklama)
        else:
            self.sonra_baslat_combobox.addItem("Favori bulunamadı", None)

    def sonra_baslat_durumu_degisti(self, state):
        """Sonra Başlat seçeneği değiştiğinde alarm saati ve combobox durumunu ayarla"""
        is_checked = (state == Qt.Checked)
        self.sonra_baslat_combobox.setEnabled(is_checked)
        if is_checked:
            # Alarm zamanı ve saati pasif hale getirilir
            self.alarm_zamani_checkbox.setChecked(False)
            self.alarm_zamani_checkbox.setEnabled(False)
            self.alarm_zamani_edit.setEnabled(False)
        else:
            allow_specific_time = True
            if self.editing_timer and not self.is_editing_favorite:
                allow_specific_time = (self.editing_timer.tekrar_mevcut_calisma == 1)
            self.alarm_zamani_checkbox.setEnabled(allow_specific_time)
            self.alarm_zamani_edit.setEnabled(self.alarm_zamani_checkbox.isChecked())

    def favorilere_ekle(self):
        """Mevcut ayarları favorilere ekle"""
        if not self.parent_app:
            QMessageBox.warning(self, "Hata", "Ana uygulama referansı bulunamadı.")
            return
        
        # Mevcut form değerlerini al
        values = self.getValues()
        
        # Açıklama kontrolü
        if not values['aciklama'].strip():
            QMessageBox.warning(self, "Hata", "Favorilere eklemek için açıklama girmelisiniz.")
            return
        
        # Favori verisi oluştur
        favori_verisi = {
            'sure': values['dakika'],
            'aciklama': values['aciklama'],
            'alarm': values['alarm'],
            'tekrar_toplam_sayi': values['tekrar_sayisi'],
            'tekrar_araligi_dakika': values['tekrar_araligi_dakika'],
            'ozel_saat_aktif_ilk_calisma': values['alarm_zamani_aktif'],
            'ozel_saat_str': values['alarm_zamani'] if values['alarm_zamani_aktif'] else None,
            'sonra_baslat_aktif': values.get('sonra_baslat_aktif', False),
            'beklenen_favori': values.get('beklenen_favori')
        }
        
        # Aynı favori var mı kontrol et
        for mevcut_favori in self.parent_app.favori_listesi:
            if (mevcut_favori['sure'] == favori_verisi['sure'] and
                mevcut_favori['aciklama'] == favori_verisi['aciklama'] and
                mevcut_favori['alarm'] == favori_verisi['alarm'] and
                mevcut_favori['tekrar_toplam_sayi'] == favori_verisi['tekrar_toplam_sayi'] and
                mevcut_favori['tekrar_araligi_dakika'] == favori_verisi['tekrar_araligi_dakika'] and
                mevcut_favori.get('ozel_saat_aktif_ilk_calisma') == favori_verisi['ozel_saat_aktif_ilk_calisma'] and
                mevcut_favori.get('ozel_saat_str') == favori_verisi['ozel_saat_str']):
                QMessageBox.information(self, "Bilgi", "Bu ayarlarda bir favori zaten mevcut.")
                return
        
        # Favorilere ekle
        self.parent_app.favori_listesi.append(favori_verisi)
        self.parent_app.ayarlari_kaydet()
        
        # Bilgi mesajı
        QMessageBox.information(self, "Başarılı", 
                            f"'{values['aciklama']}' favorilere eklendi!")
        
        # Favori listesi açıksa güncelle
        if self.parent_app.favori_listesi_widget.isVisible():
            self.parent_app.favori_listesini_guncelle()

    def degerleri_doldur(self, varsayilan_sure):
        """Form değerlerini doldur"""
        if self.editing_timer:
            self.dakika_spinner.setValue(self.editing_timer.dakika_ayari)
            self.aciklama_girisi.setText(self.editing_timer.temel_aciklama)
            
            self.alarm_secici.setCheckedDataList(self.editing_timer.alarm_dosyasi)
            
            self.tekrar_sayisi_spinner.setValue(self.editing_timer.tekrar_toplam_sayi)
            self.tekrar_araligi_spinner.setValue(self.editing_timer.tekrar_araligi_dakika)
            self.tekrar_araligi_spinner.setEnabled(self.editing_timer.tekrar_toplam_sayi > 1)

            # Özel saat ayarları (sadece ilk çalışmada veya favori düzenlemede düzenlenebilir)
            allow_specific_time_edit = (self.editing_timer.tekrar_mevcut_calisma == 1) or self.is_editing_favorite
            self.alarm_zamani_checkbox.setEnabled(allow_specific_time_edit)
            self.alarm_zamani_edit.setEnabled(False)

            if self.editing_timer.ozel_saat_aktif_ilk_calisma:
                self.alarm_zamani_checkbox.setChecked(True)
                try:
                    self.alarm_zamani_edit.setTime(QTime.fromString(self.editing_timer.ozel_saat_str, "HH:mm"))
                except:
                     self.alarm_zamani_edit.setTime(QTime.currentTime().addSecs(self.editing_timer.dakika_ayari * 60))
                if allow_specific_time_edit:
                    self.alarm_zamani_edit.setEnabled(True)
            else:
                self.alarm_zamani_checkbox.setChecked(False)
                self.alarm_zamani_edit.setTime(QTime.currentTime().addSecs(self.editing_timer.dakika_ayari * 60))

            # Sonra Başlat ayarları
            if getattr(self.editing_timer, 'sonra_baslat_aktif', False):
                self.sonra_baslat_checkbox.setChecked(True)
                beklenen = getattr(self.editing_timer, 'beklenen_favori_aciklama', None)
                if beklenen:
                    idx = self.sonra_baslat_combobox.findData(beklenen)
                    if idx >= 0:
                        self.sonra_baslat_combobox.setCurrentIndex(idx)
                    else:
                        idx = self.sonra_baslat_combobox.findText(beklenen)
                        if idx >= 0:
                            self.sonra_baslat_combobox.setCurrentIndex(idx)
        else:
            self.dakika_spinner.setValue(varsayilan_sure)
            self.alarm_zamani_edit.setTime(QTime.currentTime().addSecs(varsayilan_sure * 60))
            self.alarm_zamani_checkbox.setChecked(False)
            self.alarm_zamani_edit.setEnabled(False)
            self.sonra_baslat_checkbox.setChecked(False)
            self.sonra_baslat_combobox.setEnabled(False)

    def tekrar_ayarlarini_guncelle(self, deger):
        """Tekrar sayısı değiştiğinde tekrar aralığı spinner'ını etkinleştir/devre dışı bırak"""
        self.tekrar_araligi_spinner.setEnabled(deger > 1)

    def alarm_zamani_durumu_degisti(self, state):
        """Alarm zamanı checkbox durumu değiştiğinde QTimeEdit'i etkinleştir/devre dışı bırak"""
        self.alarm_zamani_edit.setEnabled(state == Qt.Checked)
        if state == Qt.Checked:
            self.dakika_spinner.setToolTip("Belirli bir alarm saati ayarlandığında, bu 'Dakika' değeri sonraki tekrarlar için kullanılır.")
            if self.sonra_baslat_checkbox.isChecked():
                self.sonra_baslat_checkbox.setChecked(False)
        else:
            self.dakika_spinner.setToolTip("")

    def alarm_secimi_degisti(self):
        """Alarm seçimi değiştiğinde çalmayı durdur"""
        if self.medya_oynatici.state() == QMediaPlayer.PlayingState:
            self.medya_oynatici.stop()
            self.cal_durdur_dugme.setText("Çal")
    
    def alarm_cal_durdur(self):
        """Seçili alarmı (veya çoklu seçimde rastgele birini) çal veya durdur"""
        if self.medya_oynatici.state() == QMediaPlayer.PlayingState:
            self.medya_oynatici.stop()
            self.cal_durdur_dugme.setText("Çal")
        else:
            secili_alarmlar = self.alarm_secici.checkedDataList()
            alarm_dosyasi = random.choice(secili_alarmlar) if secili_alarmlar else VARSAYILAN_ALARM_DOSYASI
            
            try:
                dosya_yolu = os.path.join(self.veri_klasoru, alarm_dosyasi)
                
                if not os.path.exists(dosya_yolu):
                    raise FileNotFoundError(f"Alarm dosyası bulunamadı: {alarm_dosyasi}")
                
                url = QUrl.fromLocalFile(dosya_yolu)
                icerik = QMediaContent(url)
                self.medya_oynatici.setMedia(icerik)
                self.medya_oynatici.play()
                self.mevcut_calma_dosyasi = alarm_dosyasi
                self.cal_durdur_dugme.setText("Durdur")
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Alarm dosyası çalınamadı: {str(e)}")
    
    def oynatici_durum_degisti(self, durum):
        """Medya oynatıcı durumu değiştiğinde çağrılır"""
        if durum == QMediaPlayer.StoppedState:
            self.cal_durdur_dugme.setText("Çal")
    
    def getValues(self):
        """Form değerlerini döndür"""
        beklenen_favori = None
        if self.sonra_baslat_checkbox.isChecked():
            beklenen_favori = self.sonra_baslat_combobox.currentData()
            if not beklenen_favori and self.sonra_baslat_combobox.count() > 0:
                beklenen_favori = self.sonra_baslat_combobox.currentText()

        secili_alarmlar = self.alarm_secici.checkedDataList()
        if not secili_alarmlar:
            alarm_degeri = VARSAYILAN_ALARM_DOSYASI
        elif len(secili_alarmlar) == 1:
            alarm_degeri = secili_alarmlar[0]
        else:
            alarm_degeri = secili_alarmlar
        
        return {
            'dakika': self.dakika_spinner.value(),
            'aciklama': self.aciklama_girisi.text() or f"Zamanlayıcı",
            'alarm': alarm_degeri,
            'tekrar_sayisi': self.tekrar_sayisi_spinner.value(),
            'tekrar_araligi_dakika': self.tekrar_araligi_spinner.value(),
            'alarm_zamani_aktif': self.alarm_zamani_checkbox.isChecked(),
            'alarm_zamani': self.alarm_zamani_edit.time().toString("HH:mm") if self.alarm_zamani_checkbox.isChecked() else None,
            'sonra_baslat_aktif': self.sonra_baslat_checkbox.isChecked(),
            'beklenen_favori': beklenen_favori
        }
    
    def closeEvent(self, event):
        """Dialog kapatıldığında çalmayı durdur"""
        self.medya_oynatici.stop()
        event.accept()
