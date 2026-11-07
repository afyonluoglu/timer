# ti_dialogs.py
import sys
import os
import re
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QMessageBox, QProgressBar, QApplication, 
                             QTextEdit, QFrame, QDesktopWidget, QListWidget)
from PyQt5.QtCore import Qt, QUrl, QTimer, QTime
from PyQt5.QtGui import QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from ti_models import format_alarm_bilgisi


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
        self.show()
        
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


class FavoriGeriYukleDialog(QDialog):
    """Yedekten geri dönülecek favorileri listeleme ve onaylama penceresi"""

    def __init__(self, favoriler, dosya_adi="", parent=None):
        """Favori geri yükleme penceresini başlatır ve arayüzü hazırlar"""
        super().__init__(parent)
        self.favoriler = favoriler
        self.dosya_adi = dosya_adi
        self.setWindowTitle("Favori Yedeğini Geri Yükle")
        self.setModal(True)
        self.resize(550, 420)
        self.init_ui()

    def init_ui(self):
        """Diyalog penceresinin bileşenlerini ve düzenini oluşturur"""
        duzen = QVBoxLayout()
        duzen.setSpacing(10)

        dosya_etiket = QLabel(f"<b>📁 Yedek Dosyası:</b> {self.dosya_adi}")
        duzen.addWidget(dosya_etiket)

        sayi_etiket = QLabel(f"<b>⭐ Bulunan Favori Sayısı:</b> {len(self.favoriler)} adet")
        duzen.addWidget(sayi_etiket)

        uyari_etiket = QLabel("⚠️ Onaylarsanız mevcut favorilerinizin yerine yukarıdaki yedek kayıtları yüklenecektir.")
        uyari_etiket.setStyleSheet("color: #d9534f; font-weight: bold;")
        duzen.addWidget(uyari_etiket)

        self.liste_widget = QListWidget()
        for fav in self.favoriler:
            if not isinstance(fav, dict):
                continue
            sure = fav.get('sure', 0)
            aciklama = fav.get('aciklama', 'Açıklama yok')

            alarm_bilgisi = format_alarm_bilgisi(fav.get('alarm'))

            tekrar_bilgisi = ""
            if fav.get('tekrar_toplam_sayi', 1) > 1:
                tekrar_bilgisi = f" (Tekrar: {fav['tekrar_toplam_sayi']} kez, {fav.get('tekrar_araligi_dakika', 10)} dk ara)"

            ozel_saat_bilgisi = ""
            if fav.get('ozel_saat_aktif_ilk_calisma') and fav.get('ozel_saat_str'):
                ozel_saat_bilgisi = f" - İlk Alarm: {fav['ozel_saat_str']}"

            sonra_baslat_bilgisi = ""
            if fav.get('sonra_baslat_aktif'):
                beklenen = fav.get('beklenen_favori')
                if beklenen:
                    sonra_baslat_bilgisi = f" [⏳ Sonra Başlat: {beklenen} bekleniyor]"
                else:
                    sonra_baslat_bilgisi = " [⏳ Sonra Başlat]"

            item_metin = f"⭐ {sure} dakika - {aciklama}{alarm_bilgisi}{tekrar_bilgisi}{ozel_saat_bilgisi}{sonra_baslat_bilgisi}"
            self.liste_widget.addItem(item_metin)

        duzen.addWidget(self.liste_widget)

        buton_duzen = QHBoxLayout()
        onayla_btn = QPushButton("Yedekten Geri Yükle")
        onayla_btn.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        onayla_btn.clicked.connect(self.accept)

        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet("padding: 6px 14px;")
        iptal_btn.clicked.connect(self.reject)

        buton_duzen.addStretch()
        buton_duzen.addWidget(iptal_btn)
        buton_duzen.addWidget(onayla_btn)
        duzen.addLayout(buton_duzen)

        self.setLayout(duzen)


