# ============================
# TIMER-01.PY
# Gereken Python Sürümü: 3.8 veya üzeri
#
# Gerekli Kütüphaneler:
#   pip install PyQt5
#   pip install dateparser
#
# ============================
# Doğal Dil ile Alarm Ekleme Örnekleri:
# TEST EDİLENLER:
#   5 dakika sonra alarm kur
#   Her gün saat 12:00'te ara öğün yap
#   5 dakika/saat/gün sonra Youtube seyret
#   Her 3 günde bir saat 12:00'da toplantı yap

#   EKLENECEKLER:
#   Yarın saat 09:00’da doktoru ara
#   Her cuma saat 17:00’de haftalık raporu gönder
#   20 Temmuz 2025 saat 14:00’de sunum yap
#   45 dakikada bir mola ver
#   Her hafta cuma günü saat 19:00’da 30 dakika kitap oku
#   Her ayın 1’inde saat 09:00’da faturaları öde

import sys
import logging
import os
import json
import datetime
import glob
import datetime
import re
import dateparser

# import time
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QListWidget, 
                           QMessageBox, QScrollArea, QFrame,
                            QDialog, QAbstractItemView,
                            QInputDialog, 
                            QComboBox, QFormLayout, QLineEdit, QDateEdit,
                           QTextEdit, QTimeEdit, QSpinBox,
                           QMenu, QMainWindow, QFileDialog, QTableWidget,
                           QTableWidgetItem, QHeaderView, QAction, 
                           QSplitter
                           )
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QTime, QDate
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QFont, QColor, QPainter
# from PyQt5.QtCore import QUrl, QSize
# import shutil
from sudoku_game import SudokuOyunu # SudokuOyunu sınıfını yeni dosyadan import et
from tetris_game import TetrisOyunu # TetrisOyunu sınıfını yeni dosyadan import et
from timer_helpers import TimerHelpers # Yardımcı fonksiyonları yeni dosyadan import et
from dialog_classes import (
    YeniZamanlayiciDialog, 
    YardimPenceresi, 
    AlarmDialog, 
    IlerlemeDialog,
    ClickableFrame
)
from timer_formatter import format_time, get_current_datetime_string 
from timer_logger import setup_logging, record_log, view_filtered_logs
from timer_file_analyzer import DosyaAnaliziPenceresi
from timer_reminder_system import Hatirlatici
from timer_reminder_ui import HatirlaticiManager
from timer_helpers import show_toast

# Veri ve log dosyası yollarını global olarak tanımla
VERI_KLASORU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "timer-data")
LOG_DOSYASI = os.path.join(VERI_KLASORU, "zamanlayici_log.txt")
os.makedirs(VERI_KLASORU, exist_ok=True)


class Zamanlayici:
    def __init__(self, id, dakika_ayari, temel_aciklama, alarm="alarm-01.mp3", baslama_zamani_ilk_kurulum=None,
                 tekrar_toplam_sayi=1, tekrar_mevcut_calisma=1, tekrar_araligi_dakika=10,
                 ozel_saat_aktif_ilk_calisma=False, ozel_saat_str=None):
        self.id = id
        self.dakika_ayari = dakika_ayari # Kullanıcının girdiği dakika (tekrarlar veya normal zamanlayıcı için)
        self.temel_aciklama = temel_aciklama
        self.calisma_durumu = True
        # baslama_zamani_ilk_kurulum: Bu zamanlayıcının ilk oluşturulduğu an. ZamanlayiciUygulamasi'nda ayarlanacak.
        self.baslama_zamani_ilk_kurulum = baslama_zamani_ilk_kurulum or datetime.datetime.now()
        self.alarm_dosyasi = alarm
        
        self.tekrar_toplam_sayi = tekrar_toplam_sayi
        self.tekrar_mevcut_calisma = tekrar_mevcut_calisma
        self.tekrar_araligi_dakika = tekrar_araligi_dakika

        self.ozel_saat_aktif_ilk_calisma = ozel_saat_aktif_ilk_calisma # İlk alarm belirli bir saatte mi çalacak?
        self.ozel_saat_str = ozel_saat_str # Belirli saat "HH:mm" formatında

        # sure ve toplam_sure, ZamanlayiciUygulamasi tarafından ilk kurulumda veya tekrar başlatıldığında ayarlanır.
        self.sure = 0  # saniye cinsinden kalan süre
        self.toplam_sure = 0 # saniye cinsinden bu döngünün toplam süresi

    def get_gorunen_aciklama(self):
        """Görüntülenecek açıklamayı döndürür, tekrar bilgisini içerir."""
        if self.tekrar_toplam_sayi > 1:
            return f"{self.temel_aciklama} ({self.tekrar_mevcut_calisma}/{self.tekrar_toplam_sayi})"
        return self.temel_aciklama

    def to_dict(self):
        """Zamanlayıcıyı sözlük olarak kaydetmek için"""
        # record_log(f"🚩 [KAYDET] Timer {self.id} - {self.temel_aciklama}: Kalan süre {self.sure}s, Kaydetme zamanı: {get_current_datetime_string()}")
        return {
            'id': self.id,
            'dakika_ayari': self.dakika_ayari,
            'toplam_sure': self.toplam_sure, 
            'sure': self.sure,
            'temel_aciklama': self.temel_aciklama,
            'baslama_zamani_ilk_kurulum': self.baslama_zamani_ilk_kurulum.isoformat(),
            'alarm_dosyasi': self.alarm_dosyasi,
            'calisma_durumu': self.calisma_durumu,
            'tekrar_toplam_sayi': self.tekrar_toplam_sayi,
            'tekrar_mevcut_calisma': self.tekrar_mevcut_calisma,
            'tekrar_araligi_dakika': self.tekrar_araligi_dakika,
            'ozel_saat_aktif_ilk_calisma': self.ozel_saat_aktif_ilk_calisma,
            'ozel_saat_str': self.ozel_saat_str,
            'son_guncelleme_zamani': datetime.datetime.now().isoformat()              
        }
    
    @classmethod
    def from_dict(cls, data):
        """Sözlükten zamanlayıcı oluşturmak için"""
        zamanlayici = cls(
            id=data['id'],
            # Eski kayıtlarda 'dakika' olabilir, yeni sistemde 'dakika_ayari'
            dakika_ayari=data.get('dakika_ayari', data.get('dakika', data.get('toplam_sure', 0) // 60)),
            temel_aciklama=data.get('temel_aciklama', data.get('aciklama', 'Zamanlayıcı')),
            alarm=data['alarm_dosyasi'],
            baslama_zamani_ilk_kurulum=datetime.datetime.fromisoformat(data['baslama_zamani_ilk_kurulum']),
            tekrar_toplam_sayi=data.get('tekrar_toplam_sayi', 1),
            tekrar_mevcut_calisma=data.get('tekrar_mevcut_calisma', 1),
            tekrar_araligi_dakika=data.get('tekrar_araligi_dakika', 10),
            ozel_saat_aktif_ilk_calisma=data.get('ozel_saat_aktif_ilk_calisma', False),
            ozel_saat_str=data.get('ozel_saat_str', None)
        )
        zamanlayici.sure = data['sure'] 
        zamanlayici.toplam_sure = data.get('toplam_sure', zamanlayici.dakika_ayari * 60) # Eski kayıtlar için fallback
        zamanlayici.calisma_durumu = data.get('calisma_durumu', True)
        
        # Son güncelleme zamanını yükle
        if 'son_guncelleme_zamani' in data:
            zamanlayici.son_guncelleme_zamani = data['son_guncelleme_zamani']
        

        # Yükleme sırasında toplam_sure'nin tutarlı olmasını sağla
        if not zamanlayici.ozel_saat_aktif_ilk_calisma or zamanlayici.tekrar_mevcut_calisma > 1:
            # Normal zamanlayıcı veya özel saatli bir zamanlayıcının tekrarı ise
            # toplam_sure, dakika_ayari'na göre olmalı.
            if zamanlayici.toplam_sure != zamanlayici.dakika_ayari * 60 : # Sadece gerekliyse düzelt
                 # Eğer dosyadaki toplam_sure, dakika_ayari ile tutarsızsa ve bu bir tekrar ise, düzelt.
                 # Bu durum genellikle eski kayıtlardan geliyorsa veya bir hata varsa oluşur.
                 # Yeni kaydedilenlerde tutarlı olmalı.
                 pass # Şimdilik bu durumu gözlemleyelim, gerekirse düzeltme eklenebilir.
        # Eğer özel saatli ilk çalışma ise, toplam_sure dosyadan geldiği gibi kalmalı (özel hesaplanmış süre).

        return zamanlayici

class AnaUygulamaPenceresi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DMAG Zamanlayıcı")
        self.resize(1100, 1350)
        
        # Merkezi widget olarak zamanlayıcı uygulamasını ayarla
        self.zamanlayici_widget = ZamanlayiciUygulamasi()
        self.setCentralWidget(self.zamanlayici_widget)
        
        # Menü çubuğu oluştur
        self.menu_olustur()
    
    def menu_olustur(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Zamanlayıcı menüsü
        zamanlayici_menu = menubar.addMenu('Zamanlayıcı')
        
        # Yeni zamanlayıcı eylemi
        yeni_zamanlayici_eylem = QAction('Yeni Zamanlayıcı Başlat', self)
        yeni_zamanlayici_eylem.setShortcut('Ctrl+T')
        yeni_zamanlayici_eylem.triggered.connect(self.zamanlayici_widget.yeni_zamanlayici_baslat)
        zamanlayici_menu.addAction(yeni_zamanlayici_eylem)
        
        # Yeni hatırlatıcı eylemi
        yeni_hatirlatici_eylem = QAction('Yeni Hatırlatıcı Ekle', self)
        yeni_hatirlatici_eylem.setShortcut('Ctrl+R')
        yeni_hatirlatici_eylem.triggered.connect(self.zamanlayici_widget.hatirlatici_manager.yeni_hatirlatici_ekle)
        zamanlayici_menu.addAction(yeni_hatirlatici_eylem)
        
        # Araçlar menüsü
        araclar_menu = menubar.addMenu('Araçlar')
        
        # Dosya analizi eylemi
        dosya_analizi_eylem = QAction('Dosya Analizi', self)
        dosya_analizi_eylem.setShortcut('Ctrl+A')
        dosya_analizi_eylem.triggered.connect(self.dosya_analizi_ac)
        araclar_menu.addAction(dosya_analizi_eylem)
        
        show_logs = QAction("Log'ları Göster", self)
        show_logs.setShortcut('Ctrl+L')
        show_logs.triggered.connect(lambda: view_filtered_logs(LOG_DOSYASI))       
        araclar_menu.addAction(show_logs)

        toast_test = QAction("Toast Test", self)
        toast_test.setShortcut('Ctrl+Alt+T')        
        toast_test.triggered.connect(lambda: show_toast(self, "Mesaj Zamanı", "Toast test mesajı", duration=0))       
        araclar_menu.addAction(toast_test)

        # Oyunlar menüsü
        oyunlar_menu = menubar.addMenu('Oyunlar')
        
        # Sudoku eylemi
        sudoku_eylem = QAction('Sudoku', self)
        sudoku_eylem.setShortcut('Ctrl+S')
        sudoku_eylem.triggered.connect(self.sudoku_ac)
        oyunlar_menu.addAction(sudoku_eylem)
        
        # Tetris eylemi
        tetris_eylem = QAction('Tetris', self)
        tetris_eylem.setShortcut('Ctrl+E')
        tetris_eylem.triggered.connect(self.tetris_ac)
        oyunlar_menu.addAction(tetris_eylem)
    
        # Yardım Menüsü
        yardim_menu = menubar.addMenu('Yardım')
        kilavuz_eylem = QAction('Kullanım Kılavuzu', self)
        kilavuz_eylem.setShortcut('F1')
        kilavuz_eylem.triggered.connect(self.yardim_goster)
        yardim_menu.addAction(kilavuz_eylem)

        # Program Hakkında menüsü
        hakkinda_eylem = QAction('Program Hakkında', self)
        hakkinda_eylem.triggered.connect(self.program_hakkinda_goster)
        yardim_menu.addAction(hakkinda_eylem)        
    
    def yardim_goster(self):
        """Yardım içeriğini timer-help.html dosyasından okuyup yeni bir pencerede gösterir."""
        
        # Betik dosyasının bulunduğu dizini al
        betik_dizini = os.path.dirname(os.path.abspath(__file__))
        yardim_dosyasi_yolu = os.path.join(betik_dizini, "timer-help.html")

        try:
            with open(yardim_dosyasi_yolu, 'r', encoding='utf-8') as dosya:
                yardim_icerigi = dosya.read()
            
            dialog = YardimPenceresi(self, "Yardım - Kullanım Kılavuzu", yardim_icerigi, html_dosya_yolu=yardim_dosyasi_yolu)
            dialog.exec_()
            
        except FileNotFoundError:
            QMessageBox.warning(self, "Hata", 
                                f"Yardım dosyası bulunamadı:\n{yardim_dosyasi_yolu}\n\n"
                                "Lütfen Python betiği ile aynı dizinde 'timer-help.html' dosyasının olduğundan emin olun.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Yardım içeriği okunurken bir hata oluştu: {str(e)}")

    def program_hakkinda_goster(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt5.QtGui import QPixmap

        dlg = QDialog(self)
        dlg.setWindowTitle("Program Hakkında")
        layout = QVBoxLayout()
        label = QLabel()
        # Dosya yolunu mutlak olarak belirle
        betik_dizini = os.path.dirname(os.path.abspath(__file__))
        webp_yolu = os.path.join(betik_dizini, "timer.webp")
        if not os.path.exists(webp_yolu):
            print("⚠️ Uyarı: timer.webp bulunamadı:", webp_yolu)        
        pixmap = QPixmap(webp_yolu)
        label.setPixmap(pixmap.scaled(450, 450, aspectRatioMode=Qt.KeepAspectRatio))
        layout.addWidget(label)

        info1 = QLabel("DMAG Zamanlayıcı Programı")
        info2 = QLabel("Versiyon: 1.0")
        info3 = QLabel("(c) 2025  - Dr. Mustafa Afyonluoğlu")
        info1.setStyleSheet("font-weight: bold; font-size: 18px; color: #760101;")

        layout.addWidget(info1)
        layout.addWidget(info2)
        layout.addWidget(info3)

        dlg.setLayout(layout)
        dlg.exec_()

    def dosya_analizi_ac(self):
        """Dosya analizi penceresini aç"""
        self.dosya_analizi_pencere = DosyaAnaliziPenceresi(self)
        self.dosya_analizi_pencere.show()
    
    def sudoku_ac(self):
        """Sudoku penceresini aç"""
        self.sudoku_pencere = SudokuOyunu(self)
        self.sudoku_pencere.show()
    
    def tetris_ac(self):
        """Tetris penceresini aç"""
        self.tetris_pencere = TetrisOyunu(self)
        self.tetris_pencere.show()

    def closeEvent(self, event):
        # Program kapatılırken ayarları kaydet
        # record_log("🚩 [KAPANIŞ] Program kapatılıyor, ayarlar kaydediliyor...")
        for timer in self.zamanlayici_widget.aktif_zamanlayicilar:
            record_log(f"☑️ [KAPANIŞ] Timer {timer.id} - '{timer.temel_aciklama}': Kalan süre {format_time(timer.sure)} kaydediliyor")

        self.zamanlayici_widget.helpers.ayarlari_kaydet()
        event.accept()
        record_log("--------------------P R O G R A M  K A P A T I L D I ------------------")

class ZamanlayiciUygulamasi(QWidget):
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

    def kisayol_tuslari_ayarla(self):
        """Klavye kısayollarını ayarla"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # F tuşu için favori kısayolu
        self.favori_kisayol = QShortcut(QKeySequence("F"), self)
        self.favori_kisayol.activated.connect(self.favorileri_goster)
        
        # G tuşu için geçmiş kısayolu
        self.gecmis_kisayol = QShortcut(QKeySequence("G"), self)
        self.gecmis_kisayol.activated.connect(self.gecmisi_goster)
        
        # ESC tuşu ile panelleri kapatma (opsiyonel)
        self.kapat_kisayol = QShortcut(QKeySequence("Escape"), self)
        self.kapat_kisayol.activated.connect(self.panelleri_kapat)

    def panelleri_kapat(self):
        """ESC tuşu ile açık panelleri kapat"""
        if self.gecmis_listesi_widget.isVisible():
            self.gecmisi_goster()
        elif self.favori_listesi_widget.isVisible():
            self.favorileri_goster()

    def alarm_dosyalarini_bul(self):
        """Timer-data klasöründeki alarm*.mp3 dosyalarını bulur"""
        try:
            self.alarm_dosyalari = []
            alarm_klasoru = self.veri_klasoru
            dosya_deseni = os.path.join(alarm_klasoru, "alarm*.mp3")
            
            for dosya_yolu in glob.glob(dosya_deseni):
                dosya_adi = os.path.basename(dosya_yolu)
                self.alarm_dosyalari.append(dosya_adi)
            
            # Varsayılan alarm dosyası bulunamadıysa uyarı ver
            if "alarm-01.mp3" not in self.alarm_dosyalari:
                record_log("❗ Uyarı: Varsayılan alarm dosyası (alarm-01.mp3) bulunamadı!", "error")
        except Exception as e:
            record_log(f"Alarm dosyaları taranırken hata: {str(e)}", "error")
            self.alarm_dosyalari = []
        
    def arayuzu_olustur(self):
        # Ana düzen
        ana_duzen = QVBoxLayout()
        
        # Başlat düğmesi
        # self.baslat_dugme = QPushButton("⏱️ Yeni Zamanlayıcı Başlat")
        # self.baslat_dugme.setStyleSheet("background-color: #760101; color: white; font-weight: bold;")  # Arkaplan kırmızı, yazı beyaz ve kalın
        # self.baslat_dugme.clicked.connect(self.yeni_zamanlayici_baslat)
        # self.baslat_dugme.setCursor(Qt.PointingHandCursor)
        # ana_duzen.addWidget(self.baslat_dugme)

        # Aktif zamanlayıcılar başlığı ve saat
        aktif_baslik_duzen = QHBoxLayout()

        aktif_baslik = QLabel("Aktif Zamanlayıcılar:")
        aktif_baslik.setFont(QFont("Arial", 12, QFont.Bold))
        aktif_baslik_duzen.addWidget(aktif_baslik)

        # Boşluk ekle
        aktif_baslik_duzen.addStretch()

        self.baslat_dugme = QPushButton("⏱️ Yeni Zamanlayıcı Başlat")
        self.baslat_dugme.setFont(QFont("Arial", 11, QFont.Bold))
        self.baslat_dugme.setFixedHeight(40) 
        self.baslat_dugme.setStyleSheet("""
            QPushButton {
                background-color: #172668;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #75d6ff;  /* Hover rengi */
                color: #004285;             /* Hover'da yazı rengi */
            }
        """)

        self.baslat_dugme.clicked.connect(self.yeni_zamanlayici_baslat)
        self.baslat_dugme.setCursor(Qt.PointingHandCursor)
        aktif_baslik_duzen.addWidget(self.baslat_dugme)

        # Boşluk ekle
        aktif_baslik_duzen.addStretch()

        # Saat etiketi
        self.saat_label = QLabel()
        self.saat_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.saat_label.setStyleSheet("color: #8d0000ff;") 
        self.saat_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        aktif_baslik_duzen.addWidget(self.saat_label)

        # Sabit yükseklik için bir QWidget'e koy
        aktif_baslik_widget = QWidget()
        aktif_baslik_widget.setLayout(aktif_baslik_duzen)
        aktif_baslik_widget.setFixedHeight(50)  # Yüksekliği sabitle (örnek: 50 piksel)

        # Ana düzene ekle
        ana_duzen.addWidget(aktif_baslik_widget)

        # Aktif zamanlayıcılar alanı
        self.aktif_zamanlayicilar_alan = QVBoxLayout()
        
        # Kaydırma alanı için bir çerçeve
        scroll_cerceve = QFrame()
        scroll_cerceve.setLayout(self.aktif_zamanlayicilar_alan)
        
        # Kaydırma alanı
        self.scroll_alan = QScrollArea()
        self.scroll_alan.setWidgetResizable(True)
        self.scroll_alan.setWidget(scroll_cerceve)
        self.scroll_alan.setMinimumHeight(150)
        self.scroll_alan.setMaximumHeight(220)
        ana_duzen.addWidget(self.scroll_alan)
        
        #Hatırlatıcı Alanı
        hatirlatici_duzen = QVBoxLayout()
        
        # Hatırlatıcı başlığı ve yeni ekleme düğmesi        
        hatirlatici_baslik_duzen = QHBoxLayout()
        hatirlatici_baslik = QLabel("Hatırlatıcılar:")
        hatirlatici_baslik.setFont(QFont("Arial", 12, QFont.Bold))
        hatirlatici_baslik_duzen.addWidget(hatirlatici_baslik)
        
        self.yeni_hatirlatici_btn = QPushButton("📅 Yeni Hatırlatıcı")
        self.yeni_hatirlatici_btn.clicked.connect(self.hatirlatici_manager.yeni_hatirlatici_ekle)
        self.yeni_hatirlatici_btn.setCursor(Qt.PointingHandCursor)
        hatirlatici_baslik_duzen.addWidget(self.yeni_hatirlatici_btn)
        
        hatirlatici_duzen.addLayout(hatirlatici_baslik_duzen)
        
        # Hatırlatıcı listeleri (yan yana)
        # hatirlatici_listeler_duzen = QHBoxLayout()
        
        # QSplitter kullanarak yeniden boyutlandırılabilir alan oluştur
        from PyQt5.QtWidgets import QSplitter
        hatirlatici_splitter = QSplitter(Qt.Horizontal)
        
        # Sol widget - Tüm hatırlatıcılar
        sol_widget = QWidget()
        sol_duzen = QVBoxLayout()
        sol_duzen.addWidget(QLabel("Tüm Hatırlatıcılar:"))
        self.tum_hatirlaticilar_list = QListWidget()
        self.tum_hatirlaticilar_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tum_hatirlaticilar_list.customContextMenuRequested.connect(self.hatirlatici_manager.hatirlatici_sag_tik_menu)
        # self.tum_hatirlaticilar_list.setMaximumHeight(220)
        self.tum_hatirlaticilar_list.setStyleSheet("""
            QListWidget {
                background-color: #e8f5e8;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #ddd;            /* Her öğe arasında ince bir çizgi */
                color: #333;                              /* Normal durum font rengi */
            }
            QListWidget::item:selected {
                background-color: #00a534;                /* Seçili öğe yeşil */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #00561b;                 /* Hover durumu */
                color: rgb(255,255,255);
                font-weight: bold;                         /* Kalın font */                                                 
            }
            QListWidget::item:selected:hover {
                background-color: #00561b;                 /* Seçili ve hover durumu */
                color: #ffff99;                            /* Seçili ve hover durumu font rengi, açık sarı */
            }                                                                                                                                                                                                                       
        """)
        sol_duzen.addWidget(self.tum_hatirlaticilar_list)
        sol_widget.setLayout(sol_duzen)
        
        # Sağ widget - Geçmiş/Yapılmamış hatırlatıcılar
        sag_widget = QWidget()
        sag_duzen = QVBoxLayout()
        sag_duzen.addWidget(QLabel("Yapılmamış Hatırlatıcılar:"))
        self.gecmis_hatirlaticilar_list = QListWidget()
        self.gecmis_hatirlaticilar_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.gecmis_hatirlaticilar_list.customContextMenuRequested.connect(self.hatirlatici_manager.gecmis_hatirlatici_sag_tik_menu)
        # self.gecmis_hatirlaticilar_list.setMaximumHeight(220)
        self.gecmis_hatirlaticilar_list.setStyleSheet("""
            QListWidget {
                background-color: #fff2f2;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #ddd;            /* Her öğe arasında ince bir çizgi */
                color: #333;                              /* Normal durum font rengi */
            }
            QListWidget::item:selected {
                background-color: #d32f2f;  /* Vibrant red for selection */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #b71c1c;  /* Darker red for hover */
                color: rgb(255,255,255);
                font-weight: bold;
            }
            QListWidget::item:selected:hover {
                background-color: #9a0007;  /* Even darker red for selected+hover */
                color: #ffff99;  /* Keeping the yellow highlight text for consistency */
            }                                                      
        """)
        sag_duzen.addWidget(self.gecmis_hatirlaticilar_list)
        sag_widget.setLayout(sag_duzen)
        
        # Widget'ları splitter'a ekle
        hatirlatici_splitter.addWidget(sol_widget)
        hatirlatici_splitter.addWidget(sag_widget)
        
        # Başlangıç oranlarını ayarla (60% sol, 40% sağ)
        hatirlatici_splitter.setSizes([700, 300])
        
        # Splitter'ın görünümünü özelleştir
        hatirlatici_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #cccccc;
                width: 3px;
                border: 1px solid #aaaaaa;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #999999;
            }
        """)
        
        # Hatırlatıcı listelerini yatay olarak yan yana yerleştir
        # hatirlatici_listeler_duzen.addLayout(sol_duzen, 3)  # ekranın %60 (3/5)
        # hatirlatici_listeler_duzen.addLayout(sag_duzen, 2)  # ekranın %40 (2/5)        
        
        # hatirlatici_duzen.addLayout(hatirlatici_listeler_duzen)
        hatirlatici_duzen.addWidget(hatirlatici_splitter)
        ana_duzen.addLayout(hatirlatici_duzen)


        # NLP Doğal Dil Girişi
        dogal_dil_duzen = QHBoxLayout()  # Yeni bir yatay düzen oluştur
        # Doğal dil girişi için alan ve buton ekle
        self.natural_input = QLineEdit()
        self.natural_input.setPlaceholderText("Doğal dilde hatırlatıcı girin: örn. 'Her gün/hafta/ay saat 12:30'da ara öğün yap   5 dakika/saat/gün sonra Youtube seyret'")
        dogal_dil_duzen.addWidget(self.natural_input)  # Düzen içine ekle

        self.natural_input_btn = QPushButton("✨ NLP ile Hatırlatıcı Oluştur")
        self.natural_input_btn.clicked.connect(self.natural_language_timer)
        dogal_dil_duzen.addWidget(self.natural_input_btn)  # Düzen içine ekle

        ana_duzen.addLayout(dogal_dil_duzen)  # Ana düzen içine yatay düzeni ekle


        # Geçmiş alanı
        gecmis_duzen = QVBoxLayout()
        
        # Geçmiş başlığı ve düğmeleri
        gecmis_baslik_duzen = QHBoxLayout()
        
        gecmis_baslik = QLabel("Zamanlayıcı Geçmişi:")
        gecmis_baslik.setFont(QFont("Arial", 12, QFont.Bold))
        gecmis_baslik_duzen.addWidget(gecmis_baslik)
        
        # Geçmiş düğmesi
        self.gecmis_dugme = QPushButton("GEÇMİŞİ GİZLE")
        self.gecmis_dugme.clicked.connect(self.gecmisi_goster)
        gecmis_baslik_duzen.addWidget(self.gecmis_dugme)
        
        # Silme düğmesi
        self.sil_dugme = QPushButton("Seçilen Geçmişi Sil")
        self.sil_dugme.clicked.connect(self.secilen_gecmisi_sil)
        self.sil_dugme.setEnabled(False)  # Başlangıçta devre dışı
        gecmis_baslik_duzen.addWidget(self.sil_dugme)
        
        gecmis_duzen.addLayout(gecmis_baslik_duzen)
        
        # Geçmiş listesi (açık olarak başlatılacak)
        self.gecmis_listesi_widget = QListWidget()
        self.gecmis_listesi_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Çoklu seçim
        self.gecmis_listesi_widget.setVisible(True)
        self.gecmis_listesi_widget.itemSelectionChanged.connect(self.gecmis_secimi_degisti)
        self.gecmis_listesi_widget.itemDoubleClicked.connect(self.gecmis_zamanlayici_baslat)  # Yeni eklenen satır
        # Background rengini değiştir
        self.gecmis_listesi_widget.setStyleSheet("""
            QListWidget {
                background-color: #ccebff;  /* Açık mavi */
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #ddd; /* Her öğe arasında ince bir çizgi */
                color: #333;  /* Normal durum font rengi */
            }
            QListWidget::item:selected {
                background-color: #007acc;  /* Seçili öğe mavi */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #004c80;  /* Hover durumu */
                color: rgb(255,255,255);
                font-weight: bold;  /* Kalın font */                                                 
            }
            QListWidget::item:selected:hover {
                background-color: #005599;  /* Seçili ve hover durumu */
                color: #ffff99;  /* Seçili ve hover durumu font rengi, açık sarı */
            }                                                 
        """)
        gecmis_duzen.addWidget(self.gecmis_listesi_widget)
        
        ana_duzen.addLayout(gecmis_duzen)
        
        # Geçmiş listesi için sağ tık menüsü
        self.gecmis_listesi_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.gecmis_listesi_widget.customContextMenuRequested.connect(self.gecmis_sag_tik_menu)
        

        # Favori alanı
        favori_duzen = QVBoxLayout()
        
        # Favori başlığı ve düğmeleri
        favori_baslik_duzen = QHBoxLayout()
        
        favori_baslik = QLabel("Favori Zamanlayıcılar:")
        favori_baslik.setFont(QFont("Arial", 12, QFont.Bold))
        favori_baslik_duzen.addWidget(favori_baslik)


        # Favori düğmesi ekle
        self.favori_dugme = QPushButton("FAVORİLERİ GİZLE")
        self.favori_dugme.clicked.connect(self.favorileri_goster)
        favori_baslik_duzen.addWidget(self.favori_dugme)

        # Favori silme düğmesi
        self.favori_sil_dugme = QPushButton("Seçilen Favorileri Sil")
        self.favori_sil_dugme.clicked.connect(self.secilen_favorileri_sil)
        self.favori_sil_dugme.setEnabled(False)
        # self.favori_sil_dugme.setVisible(False)
        favori_baslik_duzen.addWidget(self.favori_sil_dugme)

        favori_duzen.addLayout(favori_baslik_duzen)

        # Favori listesi widget'ı ekle (açık olarak başlatılacak)
        self.favori_listesi_widget = QListWidget()
        self.favori_listesi_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.favori_listesi_widget.setVisible(True)
        self.favori_listesi_widget.itemSelectionChanged.connect(self.favori_secimi_degisti)
        self.favori_listesi_widget.itemDoubleClicked.connect(self.favori_zamanlayici_baslat)
        self.favori_listesi_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.favori_listesi_widget.customContextMenuRequested.connect(self.favori_sag_tik_menu)
        self.favori_listesi_widget.setMaximumHeight(220)
        # Background rengini değiştir
        self.favori_listesi_widget.setStyleSheet("""
            QListWidget {
                background-color: #ccffdc;  /* Açık yeşil */
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 3px;
                border-bottom: 1px solid #ddd; /* Her öğe arasında ince bir çizgi */
                color: #333;  /* Normal durum font rengi */
            }
            QListWidget::item:selected {
                background-color: #00a534;  /* Seçili öğe yeşil */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #00561b;  /* Hover durumu */
                color: rgb(255,255,255);
                font-weight: bold;  /* Kalın font */                                                 
            }
            QListWidget::item:selected:hover {
                background-color: #00561b;  /* Seçili ve hover durumu */
                color: #ffff99;  /* Seçili ve hover durumu font rengi, açık sarı */
            }                                                 
        """)
        
        favori_duzen.addWidget(self.favori_listesi_widget)

        ana_duzen.addLayout(favori_duzen)

        self.setLayout(ana_duzen)

    def natural_language_timer(self):
        text = self.natural_input.text()
        params = parse_natural_timer(text)
        if not params:
            QMessageBox.warning(self, "Hatalı Komut", "Doğal dil komutu anlaşılamadı. Lütfen örneğe uygun girin.")
            return
        
        print("☑️✅   Doğal dil komutu:", params)

        hatir_date = None
        hatir_time = None
        
        # 1. `zaman` veya `tarih` anahtarında tam bir datetime nesnesi var mı?
        #    (Örn: "20 dakika sonra" veya "yarın saat 10:00")
        full_datetime = params.get("zaman") or params.get("tarih")
        if isinstance(full_datetime, datetime.datetime):
            hatir_date = full_datetime.date()
            hatir_time = full_datetime.time()
        
        # 2. Sadece saat bilgisi mi var? (Örn: "her gün saat 10:00")
        #    Bu durumda tarih olarak bugünü veya bir sonraki uygun günü almalıyız.
        elif params.get("alarm_zamani"):
            try:
                saat_str = params["alarm_zamani"]
                saat, dakika = map(int, saat_str.split(':'))
                hatir_time = datetime.time(saat, dakika)
                
                # Tarih için bugünü varsayalım. Hatırlatıcı sistemi tekrarı yönetecektir.
                hatir_date = datetime.date.today()

            except (ValueError, TypeError):
                print("Hata: Alarm zamanı ayrıştırılamadı.")
                hatir_time = None
        
        # Eğer hiçbir zaman bilgisi bulunamazsa (mantıksal bir hata),
        # hatırlatıcıyı oluşturma.
        if hatir_date is None or hatir_time is None:
            QMessageBox.warning(self, "Mantık Hatası", "Hatırlatıcı için geçerli bir zaman belirlenemedi.")
            return


        # hatırlatıcı oluştur
        self.hatirlatici_id_sayaci += 1
        aciklama = params["aciklama"]
        
        # Tarih ve tekrar ayarlarını belirle
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
            # Belirli bir tarih için (yarın veya 20 Temmuz 2025 gibi)
            tarih = params["tarih"]
        
        # Alarm saati ayarları
        alarm_saati = None
        if params["alarm_zamani_aktif"] and params["alarm_zamani"]:
            alarm_saati = params["alarm_zamani"]

        hatir_mesaj = params.get("aciklama", None)

        # print(f"   ✨ NLM:  Yeni Hatırlatıcı oluşturuluyor: Hatir_date: {hatir_date} -  Hatir_time: {hatir_time} - Hatir_mesaj: {hatir_mesaj} - {tekrar_tipi}")
        
        # Hatirlatici sınıfı QTime beklediği için datetime.time'ı QTime'a çevir
        q_hatir_time = None
        if isinstance(hatir_time, datetime.time):
            q_hatir_time = QTime(hatir_time.hour, hatir_time.minute, hatir_time.second)
                
        # Hatırlatıcı oluştur
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
        

        # Hatırlatıcıyı listeye ekle ve kaydet
        self.hatirlaticilar.append(yeni_hatirlatici)
        self.hatirlatici_manager.hatirlatici_listelerini_guncelle()
        self.ayarlari_kaydet()
        
        # Bildirim göster
        show_toast(self, 'Yeni hatırlatıcı oluşturuldu', f"{aciklama}", 15000)
        
        # Giriş alanını temizle
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
        if item:
            menu = QMenu()
            favori_duzenle_action = menu.addAction("Favoriyi Düzenle")
            favoriden_sil_action = menu.addAction("Favorilerden Sil")
            action = menu.exec_(self.favori_listesi_widget.mapToGlobal(position))
            
            if action == favori_duzenle_action:
                self.favori_duzenle(self.favori_listesi_widget.row(item))
            elif action == favoriden_sil_action:
                self.favoriden_sil(self.favori_listesi_widget.row(item))

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
        record_log(f"🚩  Favori zamanlayıcı başlatılıyor: {item.text()}")
        return self.helpers.favori_zamanlayici_baslat(item)

    def gecmis_secimi_degisti(self):
        return self.helpers.gecmis_secimi_degisti()
    
    def secilen_gecmisi_sil(self):
        return self.helpers.secilen_gecmisi_sil()
    
    def gecmisi_goster(self):
        return self.helpers.gecmisi_goster()

    def gecmis_zamanlayici_baslat(self, item):
        return self.helpers.gecmis_zamanlayici_baslat(item)

    def yeni_zamanlayici_baslat(self):
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
                ozel_saat_str=alarm_zamani_str
            )
            yeni_zamanlayici.baslama_zamani_ilk_kurulum = datetime.datetime.now()
            record_log(f"🚩 Yeni zamanlayıcı başlatılıyor: {yeni_zamanlayici.temel_aciklama} - {dakika_ayari_degeri} dakika, alarm: {alarm_dosyasi}, tekrar: {tekrar_sayisi}, aralık: {tekrar_araligi_dakika} dakika, özel saat: {alarm_zamani_str if alarm_zamani_aktif else 'Hayır'}")

            if alarm_zamani_aktif and alarm_zamani_str:
                try:
                    alarm_saati_qtime = QTime.fromString(alarm_zamani_str, "HH:mm")
                    simdiki_datetime = datetime.datetime.now()
                    
                    alarm_hedef_datetime = datetime.datetime(
                        simdiki_datetime.year, simdiki_datetime.month, simdiki_datetime.day,
                        alarm_saati_qtime.hour(), alarm_saati_qtime.minute()
                    )

                    if alarm_hedef_datetime < simdiki_datetime: # Eğer alarm saati bugün için geçmişse, yarına ayarla
                        alarm_hedef_datetime += datetime.timedelta(days=1)
                    
                    fark_saniye = int((alarm_hedef_datetime - simdiki_datetime).total_seconds())
                    
                    if fark_saniye < 0: fark_saniye = 0 

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
            
            # simdi = datetime.datetime.now()
            # self.gecmis_listesi.append({
            #     'tarih': simdi.strftime('%d.%m.%Y %H:%M:%S'),
            #     'sure': dakika_ayari_degeri, # Her zaman kullanıcının girdiği dakika
            #     'aciklama': aciklama,
            #     'alarm': alarm_dosyasi,
            #     'tekrar_toplam_sayi': tekrar_sayisi,
            #     'tekrar_araligi_dakika': tekrar_araligi_dakika,
            #     'ozel_saat_aktif_ilk_calisma': alarm_zamani_aktif, # Geçmişe de ekleyelim
            #     'ozel_saat_str': alarm_zamani_str if alarm_zamani_aktif else None
            # })
            self.son_sure = dakika_ayari_degeri
            self.ayarlari_kaydet()
            show_toast(self,'Yeni zamanlayıcı başlıtıldı', f"{yeni_zamanlayici.get_gorunen_aciklama()}", 15000)

    def zamanlayici_widget_olustur(self, zamanlayici):
        # QFrame yerine ClickableFrame kullan
        zamanlayici_cerceve = ClickableFrame(f"zamanlayici_{zamanlayici.id}")
        zamanlayici_cerceve.setObjectName(f"zamanlayici_{zamanlayici.id}")
        zamanlayici_cerceve.setFrameStyle(QFrame.Box | QFrame.Raised)
        zamanlayici_cerceve.setLineWidth(1)
        # Çift tıklama sinyalini bağla
        zamanlayici_cerceve.doubleClicked.connect(self.handle_timer_double_click_event)
        
        zamanlayici_duzen = QHBoxLayout()
        
        aciklama_etiketi = QLabel(zamanlayici.get_gorunen_aciklama())
        aciklama_etiketi.setMinimumWidth(150)
        aciklama_etiketi.setObjectName(f"aciklama_{zamanlayici.id}") # Nesne adı ekle
        zamanlayici_duzen.addWidget(aciklama_etiketi)
        
        kalan_sure_etiketi = QLabel(f"{zamanlayici.sure // 60:02d}:{zamanlayici.sure % 60:02d}")
        kalan_sure_etiketi.setObjectName(f"sure_{zamanlayici.id}")
        kalan_sure_etiketi.setAlignment(Qt.AlignCenter)
        kalan_sure_etiketi.setFont(QFont("Arial", 12, QFont.Bold))
        zamanlayici_duzen.addWidget(kalan_sure_etiketi)
        
        toplam_sure_etiketi = QLabel(f"/{zamanlayici.toplam_sure // 60:02d}:{zamanlayici.toplam_sure % 60:02d}")
        toplam_sure_etiketi.setObjectName(f"toplam_sure_{zamanlayici.id}") # Nesne adı ekle
        zamanlayici_duzen.addWidget(toplam_sure_etiketi)
        
        if zamanlayici.alarm_dosyasi != "alarm-01.mp3":
            alarm_etiketi = QLabel(f"[{zamanlayici.alarm_dosyasi}]")
            alarm_etiketi.setObjectName(f"alarm_label_{zamanlayici.id}") # Nesne adı ekle
            zamanlayici_duzen.addWidget(alarm_etiketi)
        
        self.complete_button = QPushButton("✅ Tamamlandı")
        self.complete_button.setObjectName(f"tamamlandi_{zamanlayici.id}")
        self.complete_button.clicked.connect(lambda checked, z_id=zamanlayici.id: self.zamanlayici_tamamlandi(z_id)) 
        zamanlayici_duzen.addWidget(self.complete_button)

        self.setTime_button = QPushButton("⏱️ Süre Ayarla")
        self.setTime_button.setObjectName(f"SetTime_{zamanlayici.id}")
        self.setTime_button.clicked.connect(lambda checked, z_id=zamanlayici.id: self.süre_Degistir(z_id))
        zamanlayici_duzen.addWidget(self.setTime_button)

        durdur_dugme = QPushButton("⏸️ Durdur")
        durdur_dugme.setObjectName(f"durdur_{zamanlayici.id}")
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
            
            # Zamanlayıcı özelliklerini güncelle
            target_timer.temel_aciklama = values['aciklama']
            target_timer.alarm_dosyasi = values['alarm']
            target_timer.tekrar_toplam_sayi = values['tekrar_sayisi']
            target_timer.tekrar_araligi_dakika = values['tekrar_araligi_dakika']
            
            new_dakika_ayari = values['dakika']
            new_ozel_saat_aktif = values['alarm_zamani_aktif']
            new_ozel_saat_str = values['alarm_zamani']

            timing_changed = False
            if new_ozel_saat_aktif != target_timer.ozel_saat_aktif_ilk_calisma or \
               (new_ozel_saat_aktif and new_ozel_saat_str != target_timer.ozel_saat_str) or \
               (not new_ozel_saat_aktif and new_dakika_ayari != target_timer.dakika_ayari):
                timing_changed = True

            target_timer.dakika_ayari = new_dakika_ayari
            target_timer.ozel_saat_aktif_ilk_calisma = new_ozel_saat_aktif
            target_timer.ozel_saat_str = new_ozel_saat_str if new_ozel_saat_aktif else None

            if timing_changed:
                if target_timer.ozel_saat_aktif_ilk_calisma and target_timer.ozel_saat_str and target_timer.tekrar_mevcut_calisma == 1:
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
                else: # Süreye dayalı veya tekrar eden zamanlayıcı için özel saat ayarı geçerli değil
                    target_timer.ozel_saat_aktif_ilk_calisma = False 
                    target_timer.sure = target_timer.dakika_ayari * 60
                    target_timer.toplam_sure = target_timer.dakika_ayari * 60
            
            self.guncelle_zamanlayici_widget_arayuzu(target_timer)
            self.ayarlari_kaydet()

    def guncelle_zamanlayici_widget_arayuzu(self, zamanlayici):
        """Belirli bir zamanlayıcının arayüzdeki widget'larını günceller."""
        cerceve = self.findChild(ClickableFrame, f"zamanlayici_{zamanlayici.id}") # ClickableFrame olarak bul
        if not cerceve:
            return

        aciklama_etiketi = cerceve.findChild(QLabel, f"aciklama_{zamanlayici.id}")
        if aciklama_etiketi:
            aciklama_etiketi.setText(zamanlayici.get_gorunen_aciklama())

        kalan_sure_etiketi = cerceve.findChild(QLabel, f"sure_{zamanlayici.id}")
        if kalan_sure_etiketi:
            kalan_sure_etiketi.setText(f"{zamanlayici.sure // 60:02d}:{zamanlayici.sure % 60:02d}")
        
        toplam_sure_etiketi = cerceve.findChild(QLabel, f"toplam_sure_{zamanlayici.id}")
        if toplam_sure_etiketi:
            toplam_sure_etiketi.setText(f"/{zamanlayici.toplam_sure // 60:02d}:{zamanlayici.toplam_sure % 60:02d}")

        # Alarm etiketini güncelle/ekle/kaldır
        layout = cerceve.layout()
        alarm_label_widget = cerceve.findChild(QLabel, f"alarm_label_{zamanlayici.id}")
        should_have_alarm_label = zamanlayici.alarm_dosyasi != "alarm-01.mp3"

        if should_have_alarm_label:
            new_alarm_text = f"[{zamanlayici.alarm_dosyasi}]"
            if alarm_label_widget:
                alarm_label_widget.setText(new_alarm_text)
                alarm_label_widget.setVisible(True)
            else: # Etiket yoksa, oluştur ve doğru yere ekle
                durdur_dugme = cerceve.findChild(QPushButton, f"durdur_{zamanlayici.id}")
                if durdur_dugme and layout:
                    idx = layout.indexOf(durdur_dugme)
                    if idx != -1:
                        new_alarm_label = QLabel(new_alarm_text)
                        new_alarm_label.setObjectName(f"alarm_label_{zamanlayici.id}")
                        layout.insertWidget(idx, new_alarm_label)
        elif alarm_label_widget: # Alarm etiketi olmamalı ama var
            if layout: layout.removeWidget(alarm_label_widget)
            alarm_label_widget.deleteLater()

    def zamanlayici_durdur(self, zamanlayici_id):
        for i, zamanlayici in enumerate(self.aktif_zamanlayicilar):
            if zamanlayici.id == zamanlayici_id:
                # Zamanlayıcıyı listeden kaldır
                self.aktif_zamanlayicilar.pop(i)
                record_log(f"❗❗❗Zamanlayıcı {zamanlayici.id} - '{zamanlayici.temel_aciklama}' durduruldu ve listeden kaldırıldı.", 'warning')
                # Zamanlayıcı widget'ını bul ve kaldır
                cerceve = self.findChild(QFrame, f"zamanlayici_{zamanlayici_id}")
                if cerceve:
                    self.aktif_zamanlayicilar_alan.removeWidget(cerceve)
                    cerceve.deleteLater()
                
                # Ayarları kaydet (zamanlayıcı kaldırıldıktan sonra)
                self.ayarlari_kaydet()
                break

    def zamanlayici_tamamlandi(self, zamanlayici_id):
        for i, zamanlayici in enumerate(self.aktif_zamanlayicilar):
            if zamanlayici.id == zamanlayici_id:
            # Kalan süre, erken tamamlanma süresidir (saniye cinsinden)
                erken_saniye = zamanlayici.sure
                erken_dakika = erken_saniye // 60
                erken_saniye_mod = erken_saniye % 60
                record_log(
                    f"✅ Zamanlayıcı '{zamanlayici.temel_aciklama}', {erken_dakika} dakika {erken_saniye_mod} saniye erken tamamlandı."
                    )
                zamanlayici.sure = 1 # Zamanlayıcıyı tamamlandı olarak işaretle

    def süre_Degistir(self, zamanlayici_id):
        for i, zamanlayici in enumerate(self.aktif_zamanlayicilar):
            if zamanlayici.id == zamanlayici_id:
                bilgi = self.kullanicidan_sayi_al()
                if bilgi is not None:
                    record_log(f"💫 Zamanalyıcı süresi değiştirildi: {zamanlayici.id} - '{zamanlayici.temel_aciklama}' - Yeni süre: {bilgi} dakika")
                    zamanlayici.sure = bilgi * 60

    def kullanicidan_sayi_al(self):
        girilen_sayi, ok = QInputDialog.getInt(self, 
                                               "Süre Girişi", 
                                               "Dakika olarak (0-60 arası) yeni süre:", 
                                               value=10,     # Başlangıç değeri
                                               min=0,        # Minimum değer
                                               max=60,      # Maksimum değer
                                               step=1)       # Artırma/azaltma adımı

        if ok:
            return girilen_sayi
        else:
            return None 

    def zamanlayici_guncelle(self):
        # Saati güncelle
        simdiki_zaman = QTime.currentTime()
        saat_metni = simdiki_zaman.toString("hh:mm:ss")
        self.saat_label.setText(saat_metni)

        ayarlar_degisti = False  # Ayarların değişip değişmediğini takip et
        tamamlanan_zamanlayicilar = []  # Tamamlanan zamanlayıcıları geçici bir listeye al
        
        for zamanlayici in self.aktif_zamanlayicilar[:]:  # Kopyası üzerinde döngü
            if zamanlayici.calisma_durumu:
                zamanlayici.sure -= 1
                
                sure_etiketi = self.findChild(QLabel, f"sure_{zamanlayici.id}")
                if sure_etiketi:
                    sure_etiketi.setText(format_time(zamanlayici.sure))

                
                if zamanlayici.sure <= 0:
                    # Zamanlayıcıyı hemen kaldırma, geçici listeye ekle
                    tamamlanan_zamanlayicilar.append(zamanlayici)
                    ayarlar_degisti = True

        # Tamamlanan zamanlayıcıları işle
        for zamanlayici in tamamlanan_zamanlayicilar:
            # Widget'ı kaldır
            cerceve = self.findChild(QFrame, f"zamanlayici_{zamanlayici.id}")
            if cerceve:
                self.aktif_zamanlayicilar_alan.removeWidget(cerceve)
                cerceve.deleteLater()
                
            # Geçmişe ekle
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
            
            # Alarmı çal ve sonraki tekrarı ayarla
            record_log(f"🎉 Zamanlayıcı {zamanlayici.id} - '{zamanlayici.temel_aciklama}' ({zamanlayici.tekrar_mevcut_calisma} / {zamanlayici.tekrar_toplam_sayi}) tamamlandı")
            self.alarm_cal(zamanlayici.get_gorunen_aciklama(), zamanlayici.alarm_dosyasi)
            
            # Tekrar kontrolü
            if zamanlayici.tekrar_mevcut_calisma < zamanlayici.tekrar_toplam_sayi:
                tekrar_zamanı_str = "şimdi" if zamanlayici.tekrar_araligi_dakika == 0 else f"{zamanlayici.tekrar_araligi_dakika} dakika sonra"
                record_log(f"🔁 {get_current_datetime_string()} Zamanlayıcı {zamanlayici.id} - '{zamanlayici.temel_aciklama}' {tekrar_zamanı_str} tekrar başlatılacak...")
                
                QTimer.singleShot(zamanlayici.tekrar_araligi_dakika * 60 * 1000, 
                                lambda z_info=zamanlayici: self.sonraki_tekrari_baslat(z_info))
            
            # Son olarak zamanlayıcıyı aktif listeden kaldır
            try:
                self.aktif_zamanlayicilar.remove(zamanlayici)
            except ValueError:
                pass  # Zaten kaldırılmış olabilir

        # Her 30 saniyede bir hatırlatıcı listesini güncelle
        if hasattr(self, '_son_liste_guncelleme'):
            gecen_sure = (datetime.datetime.now() - self._son_liste_guncelleme).total_seconds()
            if gecen_sure >= 30:  # 30 saniyede bir güncelle
                self.hatirlatici_manager.hatirlatici_listelerini_guncelle(kalan_sure_guncelle=True)
                self._son_liste_guncelleme = datetime.datetime.now()
        else:
            self._son_liste_guncelleme = datetime.datetime.now()

        # Hatırlatıcı kontrolünü ekle - LOG EKLENDI
        record_log("🔍 [HATIRLATICI] Hatırlatıcı kontrol döngüsü başlıyor", "debug")
        self.hatirlatici_manager.hatirlatici_kontrol()

        # Sadece değişiklik varsa ayarları kaydet
        if ayarlar_degisti:
            self.ayarlari_kaydet()

    def sonraki_tekrari_baslat(self, onceki_zamanlayici_bilgileri):
        """Belirli bir aralık sonrası bir sonraki tekrarı başlatır."""
        record_log(f"🔁 {get_current_datetime_string()}: '{onceki_zamanlayici_bilgileri.id} -{onceki_zamanlayici_bilgileri.temel_aciklama}' tekrar başlatıldı")

        tekrar_araligi_str = "(Beklemeden tekrar)" if onceki_zamanlayici_bilgileri.tekrar_araligi_dakika == 0 else f"{onceki_zamanlayici_bilgileri.tekrar_araligi_dakika} dakika"
        record_log(f"   🔸Tekrar Aralığı      : {tekrar_araligi_str}")
        record_log(f"   🔸Mevcut Tekrar #     : {onceki_zamanlayici_bilgileri.tekrar_mevcut_calisma + 1}")
        record_log(f"   🔸Toplam Tekrar Sayısı: {onceki_zamanlayici_bilgileri.tekrar_toplam_sayi}")

        self.zamanlayici_id_sayaci += 1
        yeni_tekrar_no = onceki_zamanlayici_bilgileri.tekrar_mevcut_calisma + 1
        
        yeni_zamanlayici = Zamanlayici(
            id=self.zamanlayici_id_sayaci,
            dakika_ayari=onceki_zamanlayici_bilgileri.dakika_ayari, 
            temel_aciklama=onceki_zamanlayici_bilgileri.temel_aciklama,
            alarm=onceki_zamanlayici_bilgileri.alarm_dosyasi,
            baslama_zamani_ilk_kurulum=onceki_zamanlayici_bilgileri.baslama_zamani_ilk_kurulum,
            tekrar_toplam_sayi=onceki_zamanlayici_bilgileri.tekrar_toplam_sayi,
            tekrar_mevcut_calisma=yeni_tekrar_no,
            tekrar_araligi_dakika=onceki_zamanlayici_bilgileri.tekrar_araligi_dakika,
            ozel_saat_aktif_ilk_calisma=False,
            ozel_saat_str=None
        )
        
        # Tekrarlar her zaman 'dakika_ayari' üzerinden çalışır
        yeni_zamanlayici.sure = onceki_zamanlayici_bilgileri.dakika_ayari * 60
        yeni_zamanlayici.toplam_sure = onceki_zamanlayici_bilgileri.dakika_ayari * 60
        
        self.aktif_zamanlayicilar.append(yeni_zamanlayici)
        self.zamanlayici_widget_olustur(yeni_zamanlayici)
        self.ayarlari_kaydet() # Yeni zamanlayıcı eklendiğinde kaydet

    def alarm_cal(self, aciklama, alarm_dosyasi="alarm-01.mp3"):
        """Alarmı çal ve bildirim göster"""
        mesaj = f"Zamanlayıcı süresi doldu!\nAçıklama: {aciklama}\nAlarm: {alarm_dosyasi}"
        dosya_yolu = os.path.join(self.veri_klasoru, alarm_dosyasi)
        
        # Bildirimi göstermeden önce mevcut zaman bilgisini kaydet
        gosterim_zamani = datetime.datetime.now()        

        # Dosya var mı kontrol et
        if not os.path.exists(dosya_yolu):
            # Varsayılan alarma dön
            dosya_yolu = os.path.join(self.veri_klasoru, "alarm-01.mp3")
            alarm_dosyasi = "alarm-01.mp3"
            if not os.path.exists(dosya_yolu):
                QMessageBox.warning(self, "Hata", f"Alarm dosyası bulunamadı: {alarm_dosyasi}")
                return
                
        dialog = AlarmDialog(self, "Süre Doldu", mesaj, dosya_yolu)
        record_log(f"🎵 ({aciklama}) Alarm çalınıyor: {alarm_dosyasi}")
        # open() yerine exec_() kullanıyoruz
        dialog.exec_()
        
        # Dialog kapandıktan sonra geçen süreyi hesapla
        gecen_sure = datetime.datetime.now() - gosterim_zamani
        gecen_saniye = gecen_sure.total_seconds()
        
        # Tüm aktif zamanlayıcıları güncelle
        for zamanlayici in self.aktif_zamanlayicilar:
            if zamanlayici.calisma_durumu:
                zamanlayici.sure -= int(gecen_saniye)  # Geçen süreyi çıkar
                if zamanlayici.sure < 0:
                    zamanlayici.sure = 0


    def ayarlari_kaydet(self):
        return self.helpers.ayarlari_kaydet()

    def ayarlari_yukle(self):
        """Ayarları ve aktif zamanlayıcıları yükle"""
        try:
            if os.path.exists(self.veri_dosyasi):
                with open(self.veri_dosyasi, 'r', encoding='utf-8') as dosya:
                    veri = json.load(dosya)
                    self.son_sure = veri.get('son_sure', 5)
                    self.gecmis_listesi = veri.get('gecmis', [])
                    self.favori_listesi = veri.get('favoriler', [])  # Favori listesini yükle
                    self.zamanlayici_id_sayaci = veri.get('zamanlayici_id_sayaci', 0)
                    
                    # Hatırlatıcıları yükle
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
                                # z.baslama_zamani_ilk_kurulum, z.sure, z.toplam_sure dosyadan yüklendi.

                                # Özel saatli zamanlayıcının İLK ALARMI için
                                if z.ozel_saat_aktif_ilk_calisma and z.tekrar_mevcut_calisma == 1:
                                    # Hedef saati yeniden hesapla
                                    hedef_saati_qtime = QTime.fromString(z.ozel_saat_str, "HH:mm")
                                    hedef_saati_dt = datetime.time(hedef_saati_qtime.hour(), hedef_saati_qtime.minute())
                                    
                                    # Hedef datetime'ı, zamanlayıcının orijinal oluşturulma gününe göre ayarla.
                                    # baslama_zamani_ilk_kurulum, zamanlayıcının ilk oluşturulduğu zamandır.
                                    hedef_datetime_planlanan = datetime.datetime.combine(
                                        z.baslama_zamani_ilk_kurulum.date(), 
                                        hedef_saati_dt
                                    )
                                    # Eğer planlanan hedef, ilk kurulumdan önceyse (örn. sabah 8'e kurup 9'da oluşturduysak),
                                    # hedefi bir sonraki güne al.
                                    if hedef_datetime_planlanan < z.baslama_zamani_ilk_kurulum:
                                        hedef_datetime_planlanan += datetime.timedelta(days=1)

                                    kalan_saniye_simdiye_gore = (hedef_datetime_planlanan - simdi).total_seconds()
                                    # Şimdiki zamana göre kalan süreyi hesapla
                                    if kalan_saniye_simdiye_gore > 0:
                                        z.sure = int(kalan_saniye_simdiye_gore)
                                        # toplam_sure, bu özel ilk döngünün orijinal süresi olmalı.
                                        # Bu, hedef_datetime_planlanan ile z.baslama_zamani_ilk_kurulum arasındaki farktır.
                                        z.toplam_sure = int((hedef_datetime_planlanan - z.baslama_zamani_ilk_kurulum).total_seconds())
                                        if z.toplam_sure < 0: z.toplam_sure = 0 # Negatif olmamalı
                                        
                                        self.aktif_zamanlayicilar.append(z)
                                        self.zamanlayici_widget_olustur(z)
                                        record_log(f"✅ [YÜKLE] Özel saatli Timer (ilk alarm) ekleniyor: {z.id} - '{z.temel_aciklama}', Kalan süre: {format_time(z.sure)}, Toplam süre: {format_time(z.toplam_sure)}")
                                    else:
                                        # Özel saatli ilk alarm program kapalıyken kaçırılmış/tamamlanmış.
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
                                    # Normal zamanlayıcı veya özel saatli bir zamanlayıcının tekrarı.
                                    # Ya da özel saatli ilk alarm zaten çalmış ve uygulama kapanıp açılmış.
                                    # Bu durumda, 'sure' (kalan süre) ve 'toplam_sure' (o döngünün toplam süresi)
                                    # dosyadan geldiği gibi kullanılır. Program kapalıyken geçen süreyi düşürmemiz gerekir.

                                    # record_log(f"➕ [YÜKLE] Timer {z.id} - '{z.temel_aciklama}': Dosyadan okunan kalan süre: {format_time(z.sure)}, Toplam süre: {format_time(z.toplam_sure)}")
                                    # Normal zamanlayıcı - geçen süreyi hesapla
                                    if 'son_guncelleme_zamani' in z_veri:
                                        try:
                                            son_guncelleme = datetime.datetime.fromisoformat(z_veri['son_guncelleme_zamani'])
                                            gecen_sure = int((simdi - son_guncelleme).total_seconds())
                                            # record_log(f"⚡[YÜKLE] Timer {z.id} - {z.temel_aciklama}: Son güncelleme: {z_veri['son_guncelleme_zamani']}")
                                            # record_log(f"⚡[YÜKLE] Timer {z.id} - {z.temel_aciklama}: Şimdiki zaman : {get_current_datetime_string()}")
                                            # record_log(f"⚡[YÜKLE] Timer {z.id} - {z.temel_aciklama}: Geçen süre    : {gecen_sure}s")
                                            # record_log(f"⚡[YÜKLE] Timer {z.id} - {z.temel_aciklama}: Hesaplanan kalan süre: {format_time(z.sure - gecen_sure)}")

                                            z.sure = max(0, z.sure - gecen_sure)
                                        except Exception as e:
                                            record_log(f"Zaman hesaplama hatası: {e}", "error")
                                    else:
                                        record_log(f"❗ [UYARI] Timer {z.id} - '{z.temel_aciklama}': son_guncelleme_zamani bulunamadı, süre düşürülmeyecek", "warning")
                                    

                                    record_log("⏰ Tamamlanmamış alarmlar için kalan süre hesaplanıyor...")    
                                    if z.sure > 0:
                                        # Eğer bu bir tekrar ise ve toplam_sure tutarsızsa, düzelt.
                                        if z.tekrar_mevcut_calisma > 1 and z.toplam_sure != z.dakika_ayari * 60:
                                            z.toplam_sure = z.dakika_ayari * 60
                                            if z.sure > z.toplam_sure:
                                                z.sure = z.toplam_sure
                                        record_log(f"✅ [YÜKLE] Timer {z.id} - '{z.temel_aciklama}': Zamanlayıcı aktif olarak ekleniyor, kalan süre: {format_time(z.sure)}")
                                        self.aktif_zamanlayicilar.append(z)
                                        self.zamanlayici_widget_olustur(z)
                                    else:
                                        record_log(f"➖ [YÜKLE] Timer {z.id} - '{z.temel_aciklama}': Süre dolmuş, geçmişe ekleniyor", "warning")
                                        # Süre dolmuş, geçmişe ekle
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
            else:
                self.son_sure = 5
                self.gecmis_listesi = []
                self.favori_listesi = []  # Favori listesini başlat

            # Hatırlatıcı listelerini güncelle
            self.hatirlatici_manager.hatirlatici_listelerini_guncelle()            
        except Exception as e:
            record_log(f"❗ Ayarlar yüklenemedi (dış döngü): {str(e)}", "error")
            self.son_sure = 5
            self.gecmis_listesi = []
            self.favori_listesi = []  # Favori listesini başlat

# Doğal dilde alarm komutlarını gelişmiş şekilde analiz eden fonksiyon
def parse_natural_timer(text):
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
        saat = simdi + datetime.timedelta(minutes = dakika)
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

        # Tarih ve saat bilgilerini ayrıştır
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

        # Tekrar aralığını ve zamanı ayrıştır
        tekrar_araligi_gun = int(match.group(1))
        hour = int(match.group(2))
        minute = int(match.group(3))
        aciklama = match.group(4).strip() or "Doğal Komut"

        # Başlangıç tarihini bugünden başlat
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

    # Hiçbiri eşleşmezse None döndür
    print("❌ Doğal Dil İşleme: Hiçbir eşleşme bulunamadı.")
    return None



if __name__ == "__main__":
    setup_logging(LOG_DOSYASI)
    app = QApplication(sys.argv)
    pencere = AnaUygulamaPenceresi()
    pencere.show()
    sys.exit(app.exec_())