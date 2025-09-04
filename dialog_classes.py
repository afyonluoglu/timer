# dialog_classes.py
import sys
import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                           QSpinBox, QLineEdit, QCheckBox, QTimeEdit, QComboBox, 
                           QPushButton, QLabel, QMessageBox, QProgressBar, QFrame,
                           QScrollArea, QApplication, QTextEdit)  
from PyQt5.QtCore import Qt, QTime, QUrl, QTimer
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import re

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
        self.alarm_dosyalari = alarm_dosyalari or []
        self.parent_app = parent
        self.veri_klasoru = veri_klasoru
        self.editing_timer = zamanlayici_to_edit

        if self.editing_timer:
            if self.is_editing_favorite:
                self.setWindowTitle("Favoriyi Düzenle")
            else:
                self.setWindowTitle("Zamanlayıcıyı Düzenle")
        else:
            self.setWindowTitle("Yeni Zamanlayıcı")

        self.resize(400, 320)
        
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

        alarm_duzen = QHBoxLayout()
        self.alarm_secici = QComboBox()
        self.alarm_secici.addItem("Varsayılan (alarm-01.mp3)", "alarm-01.mp3")
        for dosya in self.alarm_dosyalari:
            if dosya != "alarm-01.mp3":
                self.alarm_secici.addItem(dosya, dosya)
        self.alarm_secici.currentIndexChanged.connect(self.alarm_secimi_degisti)
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
            'ozel_saat_str': values['alarm_zamani'] if values['alarm_zamani_aktif'] else None
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
            
            index = self.alarm_secici.findData(self.editing_timer.alarm_dosyasi)
            if index >= 0:
                self.alarm_secici.setCurrentIndex(index)
            
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
        else:
            self.dakika_spinner.setValue(varsayilan_sure)
            self.alarm_zamani_edit.setTime(QTime.currentTime().addSecs(varsayilan_sure * 60))
            self.alarm_zamani_checkbox.setChecked(False)
            self.alarm_zamani_edit.setEnabled(False)

    def tekrar_ayarlarini_guncelle(self, deger):
        """Tekrar sayısı değiştiğinde tekrar aralığı spinner'ını etkinleştir/devre dışı bırak"""
        self.tekrar_araligi_spinner.setEnabled(deger > 1)

    def alarm_zamani_durumu_degisti(self, state):
        """Alarm zamanı checkbox durumu değiştiğinde QTimeEdit'i etkinleştir/devre dışı bırak"""
        self.alarm_zamani_edit.setEnabled(state == Qt.Checked)
        if state == Qt.Checked:
            self.dakika_spinner.setToolTip("Belirli bir alarm saati ayarlandığında, bu 'Dakika' değeri sonraki tekrarlar için kullanılır.")
        else:
            self.dakika_spinner.setToolTip("")

    def alarm_secimi_degisti(self):
        """Alarm seçimi değiştiğinde çalmayı durdur"""
        if self.medya_oynatici.state() == QMediaPlayer.PlayingState:
            self.medya_oynatici.stop()
            self.cal_durdur_dugme.setText("Çal")
    
    def alarm_cal_durdur(self):
        """Seçili alarmı çal veya durdur"""
        if self.medya_oynatici.state() == QMediaPlayer.PlayingState:
            self.medya_oynatici.stop()
            self.cal_durdur_dugme.setText("Çal")
        else:
            alarm_dosyasi = self.alarm_secici.currentData()
            
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
        return {
            'dakika': self.dakika_spinner.value(),
            'aciklama': self.aciklama_girisi.text() or f"Zamanlayıcı",
            'alarm': self.alarm_secici.currentData(),
            'tekrar_sayisi': self.tekrar_sayisi_spinner.value(),
            'tekrar_araligi_dakika': self.tekrar_araligi_spinner.value(),
            'alarm_zamani_aktif': self.alarm_zamani_checkbox.isChecked(),
            'alarm_zamani': self.alarm_zamani_edit.time().toString("HH:mm") if self.alarm_zamani_checkbox.isChecked() else None
        }
    
    def closeEvent(self, event):
        """Dialog kapatıldığında çalmayı durdur"""
        self.medya_oynatici.stop()
        event.accept()

class IlerlemeDialog(QDialog):
    """İlerleme gösterge dialogu"""
    
    def __init__(self, parent=None, baslik="İşlem Yapılıyor..."):
        super().__init__(parent)
        self.setWindowTitle(baslik)
        self.setModal(True)
        self.resize(300, 150)
        
        # İptal bayrağı
        self.iptal_edildi = False
        
        duzen = QVBoxLayout()
        
        self.mesaj_etiketi = QLabel("İşlem başlatılıyor...")
        duzen.addWidget(self.mesaj_etiketi)
        
        self.ilerleme_cubugu = QProgressBar()
        self.ilerleme_cubugu.setRange(0, 100)  # 0-100 arası yüzde
        self.ilerleme_cubugu.setValue(0)
        duzen.addWidget(self.ilerleme_cubugu)
        
        # İptal düğmesi
        self.iptal_dugme = QPushButton("İptal")
        self.iptal_dugme.clicked.connect(self.iptal_et)
        duzen.addWidget(self.iptal_dugme)
        
        self.setLayout(duzen)
    
    def mesaj_guncelle(self, mesaj):
        """İlerleme mesajını güncelle"""
        self.mesaj_etiketi.setText(mesaj)
        QApplication.processEvents()  # UI'yi güncelle
    
    def ilerleme_guncelle(self, yuzde, mesaj=None):
        """İlerleme çubuğunu ve mesajı güncelle"""
        self.ilerleme_cubugu.setValue(max(0, min(100, yuzde)))
        if mesaj:
            self.mesaj_guncelle(mesaj)
        QApplication.processEvents()  # UI'yi güncelle
    
    def islem_sayaci_guncelle(self, mevcut, toplam):
        """İşlem sayacını güncelle ve yüzde hesapla"""
        if toplam > 0:
            yuzde = int((mevcut / toplam) * 100)
            self.ilerleme_guncelle(yuzde, f"İşlem {mevcut}/{toplam}")
        else:
            self.ilerleme_guncelle(0, "İşlem başlatılıyor...")
    
    def iptal_et(self):
        """İptal işlemini başlat"""
        self.iptal_edildi = True
        self.mesaj_guncelle("İptal ediliyor...")
        self.iptal_dugme.setEnabled(False)
        self.accept() 
    
    def closeEvent(self, event):
        """Dialog kapatıldığında iptal bayrağını ayarla"""
        # self.iptal_edildi = True
        event.accept()

class YardimPenceresi(QDialog):
    """Yardım penceresi"""
    
    def __init__(self, parent=None, baslik="Yardım", icerik="", html_dosya_yolu=None):
        super().__init__(parent)
        self.setWindowTitle(baslik)
        self.resize(1200, 1000)
        
        duzen = QVBoxLayout()
        # QLabel yerine QTextEdit kullanın
        self.metin_alani = QTextEdit()
        self.metin_alani.setReadOnly(True) # Sadece okunabilir yap
        
        # Eğer içerik varsa HTML olarak ayarla
        if icerik and html_dosya_yolu:
            icerik = self._fix_image_paths(icerik, html_dosya_yolu)
            self.metin_alani.setHtml(icerik)
        else:
            # Varsayılan bir içerik (opsiyonel, normalde timer-help.html'den gelecek)
            self.metin_alani.setHtml("""
                <h2>Zamanlayıcı Uygulaması Yardımı</h2>
                <p>Yardım içeriği yüklenemedi.</p>
            """)
        
        duzen.addWidget(self.metin_alani) # QScrollArea'ya gerek kalmaz, QTextEdit kendi kaydırmasına sahip
        
        kapat_dugme = QPushButton("Kapat")
        kapat_dugme.clicked.connect(self.close)
        duzen.addWidget(kapat_dugme)
        
        self.setLayout(duzen)

    def _fix_image_paths(self, html, html_path):
        """HTML içindeki <img src="..."> yollarını mutlak dosya yoluna çevirir"""
        base_dir = os.path.dirname(os.path.abspath(html_path))
        def repl(match):
            src = match.group(1)
            # Eğer zaten mutlak yol ise dokunma
            if os.path.isabs(src):
                return f'src="{src}"'
            abs_path = os.path.join(base_dir, src)
            abs_path = abs_path.replace("\\", "/")  # PyQt için
            return f'src="file:///{abs_path}"'
        return re.sub(r'src="([^"]+)"', repl, html)
        
class AlarmDialog(QDialog):
    """Alarm dialogu - QDialog'dan türetilmiş özel dialog"""
    def __init__(self, parent=None, title="Alarm", message="", ses_dosyasi=""):
        super().__init__(parent)
        
        # Temel pencere ayarları
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(450, 280)  # Biraz daha büyük minimum
        self.resize(550, 320)  # Başlangıç boyutu daha büyük
        
        # Pencereyi her zaman en üstte tut
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.WindowSystemMenuHint)
                
        # Ses dosyasını sakla
        self.ses_dosyasi = ses_dosyasi
        self.medya_oynatici = None
        self.ses_caliniyor = False
        
        self.sure_baslangic = None
        self.sure_timer = None
        self.sure_label = None

        self.arayuz_olustur(message)
        
        self.sure_baslangic = QTime.currentTime()
        self.sure_timer = QTimer(self)
        self.sure_timer.timeout.connect(self.sure_guncelle)
        self.sure_timer.start(1000)  # Her saniye güncelle
                
        # Dialog'u ortalama işlemini geciktir
        QTimer.singleShot(200, self.center_dialog)
        
        # Sesi başlat (dialog tamamen yüklendikten sonra)
        QTimer.singleShot(300, self.sesi_baslat)

    def arayuz_olustur(self, message):
        """Dialog arayüzünü oluştur"""
        ana_layout = QVBoxLayout()
        ana_layout.setSpacing(20)
        ana_layout.setContentsMargins(25, 25, 25, 25)
        
        # Üst kısım - Başlık ve ikon
        ust_layout = QHBoxLayout()
        
        # Alarm ikonu (Unicode karakteri)
        ikon_label = QLabel("⏰")
        ikon_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                color: #ff6b6b;
                margin-right: 10px;
            }
        """)
        ikon_label.setFixedSize(50, 40)  # Sabit boyut
        ust_layout.addWidget(ikon_label)
        
        # Başlık
        baslik_label = QLabel("SÜRE DOLDU!")
        baslik_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #ff6b6b;
            }
        """)
        ust_layout.addWidget(baslik_label)
        ust_layout.addStretch()
        
        ana_layout.addLayout(ust_layout)
        
        # Mesaj alanı - Font boyutu düzeltildi
        mesaj_frame = QFrame()
        mesaj_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        mesaj_frame.setMinimumHeight(100)  # Daha yüksek minimum
        mesaj_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        mesaj_layout = QVBoxLayout()
        mesaj_layout.setContentsMargins(15, 15, 15, 15)  # Daha fazla padding
        mesaj_label = QLabel(message)
        mesaj_label.setWordWrap(True)
        mesaj_label.setAlignment(Qt.AlignCenter)
        mesaj_label.setMinimumHeight(60)  # Daha yüksek minimum
        
        # Font boyutunu direkt QFont ile ayarla
        font = QFont("Arial", 12)  # 12 punto font
        font.setWeight(QFont.Normal)
        mesaj_label.setFont(font)
        
        mesaj_label.setStyleSheet("""
            QLabel {
                color: #333333;
                background: transparent;
                border: none;
                padding: 10px;
            }
        """)
        mesaj_layout.addWidget(mesaj_label)
        mesaj_frame.setLayout(mesaj_layout)
        
        ana_layout.addWidget(mesaj_frame)
        
        # Sayaç etiketi ekle (ekranın üst kısmına)
        self.sure_label = QLabel("Geçen Süre: 00:00")
        self.sure_label.setAlignment(Qt.AlignCenter)
        self.sure_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #007bff;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        ana_layout.addWidget(self.sure_label)

        # Esnek boşluk
        ana_layout.addStretch()
        
        # Düğme alanı
        dugme_frame = QFrame()
        dugme_layout = QHBoxLayout()
        dugme_layout.setSpacing(15)
        
        # Sessiz düğmesi  
        self.sessiz_dugme = QPushButton("🔇 Sessiz")
        self.sessiz_dugme.setMinimumHeight(45)
        self.sessiz_dugme.setMinimumWidth(130)
        # Düğme fontunu da ayarla
        dugme_font = QFont("Arial", 12)
        dugme_font.setWeight(QFont.Bold)
        self.sessiz_dugme.setFont(dugme_font)
        self.sessiz_dugme.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #e55353;
            }
            QPushButton:pressed {
                background-color: #d93939;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.sessiz_dugme.clicked.connect(self.sesi_durdur)
        dugme_layout.addWidget(self.sessiz_dugme)
        
        # Tamam düğmesi
        tamam_dugme = QPushButton("✓ Tamam")
        tamam_dugme.setMinimumHeight(45)
        tamam_dugme.setMinimumWidth(130)
        tamam_dugme.setFont(dugme_font)  # Aynı font
        tamam_dugme.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        tamam_dugme.clicked.connect(self.accept)
        tamam_dugme.setDefault(True)  # Enter tuşu ile tetiklenebilir
        tamam_dugme.setFocus()  # İlk odak bu düğmede
        dugme_layout.addWidget(tamam_dugme)
        
        dugme_frame.setLayout(dugme_layout)
        ana_layout.addWidget(dugme_frame)
        
        self.setLayout(ana_layout)

    def sure_guncelle(self):
        """Geçen süreyi güncelle"""
        if self.sure_baslangic:
            elapsed = self.sure_baslangic.secsTo(QTime.currentTime())
            dakika = elapsed // 60
            saniye = elapsed % 60
            self.sure_label.setText(f"Geçen Süre: {dakika:02d}:{saniye:02d}")

    def center_dialog(self):
        """ Dialog'u ekranın ortasına yerleştir """
        # Önce pencereyi göster ki gerçek boyutları alabilelim
        self.show()
        
        # QDesktopWidget kullanarak ekran boyutunu al
        from PyQt5.QtWidgets import QDesktopWidget, QApplication
        
        # Ana ekranı al
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry()  # Görev çubuğu hariç alan
        
        # Dialog boyutunu al
        dialog_rect = self.geometry()
        
        # Orta noktayı hesapla
        x = (screen_rect.width() - dialog_rect.width()) // 2
        y = (screen_rect.height() - dialog_rect.height()) // 2
        
        # Pozisyonu ayarla
        self.move(x, y)
        
        # Pencereyi en öne getir
        self.raise_()
        self.activateWindow()

    def force_update(self):
            """Pencereyi zorla güncelle"""
            self.update()
            self.repaint()

    def sesi_baslat(self):
        """Alarm sesini çalmaya başlar"""
        if self.ses_dosyasi and os.path.exists(self.ses_dosyasi):
            try:
                self.medya_oynatici = QMediaPlayer()
                url = QUrl.fromLocalFile(os.path.abspath(self.ses_dosyasi))
                content = QMediaContent(url)
                self.medya_oynatici.setMedia(content)
                
                # Ses seviyesini ayarla
                self.medya_oynatici.setVolume(85)
                
                # Döngüde çalsın
                self.medya_oynatici.mediaStatusChanged.connect(self.medya_durumu_degisti)
                
                self.medya_oynatici.play()
                self.ses_caliniyor = True
                
                # Ses durumunu güncelle
                self.sessiz_dugme.setText("🔇 Sessiz (Çalıyor)")
                
            except Exception as e:
                print(f"Alarm sesi çalınırken hata: {e}")
                self.sessiz_dugme.setText("🔇 Ses Hatası")
                self.sessiz_dugme.setEnabled(False)
    
    def medya_durumu_degisti(self, durum):
        """Medya durumu değiştiğinde döngü için kontrol"""
        if (durum == QMediaPlayer.EndOfMedia and 
            self.ses_caliniyor and 
            self.medya_oynatici):
            # Ses bitti, 5 dakika sonra tekrar başlat (döngü)
            QTimer.singleShot(5 * 60 * 1000, lambda: (
                        self.medya_oynatici.setPosition(0),
                        self.medya_oynatici.play()
                    ))            
            # self.medya_oynatici.setPosition(0)
            # self.medya_oynatici.play()
    
    def sesi_durdur(self):
        """Alarm sesini durdur"""
        if self.medya_oynatici and self.ses_caliniyor:
            self.medya_oynatici.stop()
            self.ses_caliniyor = False
            self.sessiz_dugme.setText("🔇 Ses Durduruldu")
            self.sessiz_dugme.setEnabled(False)
    
    def keyPressEvent(self, event):
        """Klavye olaylarını yakala"""
        if event.key() == Qt.Key_Escape:
            # ESC tuşu ile sadece sesi durdur, pencereyi kapatma
            if self.ses_caliniyor:
                self.sesi_durdur()
            return
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter ile tamam
            self.accept()
            return
        elif event.key() == Qt.Key_Space:
            # Space ile sessiz
            if self.ses_caliniyor:
                self.sesi_durdur()
            return
        
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Dialog kapatılırken sesi durdur"""
        if self.medya_oynatici and self.ses_caliniyor:
            self.medya_oynatici.stop()
            self.ses_caliniyor = False

        if self.sure_timer:
            self.sure_timer.stop()
        super().closeEvent(event)
    
    def accept(self):
        """Tamam düğmesine basıldığında"""
        if self.medya_oynatici and self.ses_caliniyor:
            self.medya_oynatici.stop()
            self.ses_caliniyor = False
        if self.sure_timer:
            self.sure_timer.stop()
        super().accept()
    
    def reject(self):
        """İptal veya X düğmesine basıldığında"""
        if self.sure_timer:
            self.sure_timer.stop()        
        if self.medya_oynatici and self.ses_caliniyor:
            self.medya_oynatici.stop()
            self.ses_caliniyor = False
        super().reject()

