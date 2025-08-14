from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QFileDialog, QTableWidget,
                           QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import os
from timer_logger import record_log
from dialog_classes import IlerlemeDialog

class DosyaAnaliziPenceresi(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dosya Analizi")
        self.resize(800, 1200)
        
        # Merkezi widget
        merkez_widget = QWidget()
        self.setCentralWidget(merkez_widget)
        
        # Ana düzen
        ana_duzen = QVBoxLayout()
        merkez_widget.setLayout(ana_duzen)
        
        # Üst kısım
        ust_duzen = QHBoxLayout()
        
        # Klasör seç düğmesi
        self.klasor_sec_dugme = QPushButton("Klasör Seç")
        self.klasor_sec_dugme.clicked.connect(self.klasor_sec)
        ust_duzen.addWidget(self.klasor_sec_dugme)
        
        # Üst klasöre git düğmesi
        self.ust_klasor_dugme = QPushButton("Üst")
        self.ust_klasor_dugme.clicked.connect(self.ust_klasore_git)
        self.ust_klasor_dugme.setEnabled(False)
        ust_duzen.addWidget(self.ust_klasor_dugme)
        
        # Mevcut klasör etiketi
        self.mevcut_klasor_etiket = QLabel("Henüz klasör seçilmedi")
        self.mevcut_klasor_etiket.setStyleSheet("font-weight: bold;")
        ust_duzen.addWidget(self.mevcut_klasor_etiket)
        
        ust_duzen.addStretch()
        
        ana_duzen.addLayout(ust_duzen)
        
        # Tablo
        self.tablo = QTableWidget()
        self.tablo.setColumnCount(3)
        self.tablo.setHorizontalHeaderLabels(["Klasör Adı", "Boyut", "Dosya Sayısı"])
        self.tablo.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tablo.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tablo.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tablo.verticalHeader().setVisible(False)
        self.tablo.itemDoubleClicked.connect(self.klasore_git)
        ana_duzen.addWidget(self.tablo)
        
        # Mevcut klasör yolu
        self.mevcut_klasor = None
        self.klasor_gecmisi = []
        
        # Son seçilen klasör
        self.son_secilen_klasor = os.path.expanduser("~")
    
    def klasor_sec(self):
        """Klasör seçme diyaloğunu göster"""
        klasor = QFileDialog.getExistingDirectory(
            self,
            "Analiz Edilecek Klasörü Seçin",
            self.son_secilen_klasor,  # Son seçilen klasörden başla
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if klasor:
            self.son_secilen_klasor = klasor  # Son seçilen klasörü güncelle
            self.mevcut_klasor = klasor
            self.klasor_analizi_yap()
            
            is_kok_dizin = (os.path.dirname(self.mevcut_klasor) == self.mevcut_klasor)
            self.ust_klasor_dugme.setEnabled(not is_kok_dizin)
    
    def klasore_git(self, item):
        """Tabloda seçilen klasöre git"""
        if item.column() == 0:  # Sadece klasör adı sütununa tıklandığında
            yeni_klasor = os.path.join(self.mevcut_klasor, item.text())
            if os.path.isdir(yeni_klasor):
                self.mevcut_klasor = yeni_klasor
                self.klasor_analizi_yap()
                
                # Alt klasöre geçildiğinde üst tuşunu etkinleştir
                self.ust_klasor_dugme.setEnabled(True)
    
    def ust_klasore_git(self):
        """Bir üst klasöre git"""
        if self.mevcut_klasor:
            ust_klasor = os.path.dirname(self.mevcut_klasor)
            if os.path.exists(ust_klasor):
                self.mevcut_klasor = ust_klasor
                self.klasor_analizi_yap()
                
                # Kök dizine geldiysek üst tuşunu devre dışı bırak
                # Windows için sürücü kökü (örn: "C:\\") veya Unix için "/"
                is_kok_dizin = (os.path.dirname(self.mevcut_klasor) == self.mevcut_klasor)
                self.ust_klasor_dugme.setEnabled(not is_kok_dizin)
    
    def boyut_formatla(self, boyut):
        """Boyutu okunabilir formata dönüştür"""
        for birim in ['B', 'KB', 'MB', 'GB', 'TB']:
            if boyut < 1024.0:
                return f"{boyut:.1f} {birim}"
            boyut /= 1024.0
        return f"{boyut:.1f} PB"
    
    def klasor_boyutu_ve_dosya_sayisi_hesapla(self, klasor_yolu, ilerleme_dialog=None):
        """Klasörün toplam boyutunu ve dosya sayısını hesapla"""
        toplam_boyut = 0
        dosya_sayisi = 0
        islenen_oge_sayisi = 0
        
        try:
            # Önce toplam öge sayısını bul
            toplam_oge_sayisi = sum([len(files) for _, _, files in os.walk(klasor_yolu)])
            
            for yol, klasorler, dosyalar in os.walk(klasor_yolu):
                if ilerleme_dialog and ilerleme_dialog.iptal_edildi:
                    return 0, 0
                
                for dosya in dosyalar:
                    if ilerleme_dialog and ilerleme_dialog.iptal_edildi:
                        return 0, 0
                    
                    dosya_yolu = os.path.join(yol, dosya)
                    try:
                        toplam_boyut += os.path.getsize(dosya_yolu)
                        dosya_sayisi += 1
                        
                        # İlerlemeyi güncelle
                        if ilerleme_dialog:
                            islenen_oge_sayisi += 1
                            yuzde = min(int((islenen_oge_sayisi / toplam_oge_sayisi) * 100), 100)
                            ilerleme_dialog.ilerleme_guncelle(
                                yuzde,
                                f"Analiz ediliyor: {dosya} ({islenen_oge_sayisi}/{toplam_oge_sayisi})"
                            )
                    
                    except (OSError, FileNotFoundError):
                        continue
        
        except (OSError, PermissionError):
            return 0, 0
        
        return toplam_boyut, dosya_sayisi
    
    def mevcut_klasor_dosyalarini_analiz_et(self):
        """Mevcut klasördeki dosyaların (alt klasörler hariç) toplam boyutunu hesapla"""
        toplam_boyut = 0
        dosya_sayisi = 0
        
        try:
            for oge in os.listdir(self.mevcut_klasor):
                tam_yol = os.path.join(self.mevcut_klasor, oge)
                if os.path.isfile(tam_yol):
                    try:
                        toplam_boyut += os.path.getsize(tam_yol)
                        dosya_sayisi += 1
                    except (OSError, FileNotFoundError):
                        continue
        except (OSError, PermissionError):
            return 0, 0
        
        return toplam_boyut, dosya_sayisi
    
    def klasor_analizi_yap(self):
        """Mevcut klasörün analizini yap ve tabloda göster"""
        if not self.mevcut_klasor:
            return
        
        # Başlığı güncelle
        self.mevcut_klasor_etiket.setText(f"Klasör: {self.mevcut_klasor}")
        
        try:
            # İlerleme penceresini oluştur
            ilerleme = IlerlemeDialog(self, "Klasör Analizi")
            ilerleme.show()
            
            # Alt klasörleri listele
            alt_klasorler = []
            klasor_listesi = [d for d in os.listdir(self.mevcut_klasor) 
                            if os.path.isdir(os.path.join(self.mevcut_klasor, d))]
            
            # Toplam işlem sayısını ayarla (alt klasörler + mevcut klasör)
            ilerleme.islem_sayaci_guncelle(0, len(klasor_listesi) + 1)
            
            for i, oge in enumerate(klasor_listesi, 1):
                if ilerleme.iptal_edildi:
                    return
                
                tam_yol = os.path.join(self.mevcut_klasor, oge)
                if os.path.isdir(tam_yol):
                    ilerleme.islem_sayaci_guncelle(i, len(klasor_listesi) + 1)
                    boyut, dosya_sayisi = self.klasor_boyutu_ve_dosya_sayisi_hesapla(
                        tam_yol, ilerleme
                    )
                    alt_klasorler.append((oge, boyut, dosya_sayisi))
            
            # Mevcut klasördeki dosyaların analizi
            ilerleme.islem_sayaci_guncelle(len(klasor_listesi) + 1, len(klasor_listesi) + 1)
            mevcut_boyut, mevcut_dosya_sayisi = self.mevcut_klasor_dosyalarini_analiz_et()
            
            # Toplam boyut ve dosya sayısını hesapla
            toplam_boyut = mevcut_boyut + sum(klasor[1] for klasor in alt_klasorler)
            toplam_dosya = mevcut_dosya_sayisi + sum(klasor[2] for klasor in alt_klasorler)
            
            # İlerleme penceresini kapat
            ilerleme.close()
            
            if ilerleme.iptal_edildi:
                record_log("Klasör analizi iptal edildi.", "warning")
                return


            # Boyuta göre sırala (büyükten küçüğe)
            alt_klasorler.sort(key=lambda x: x[1], reverse=True)
            
            # Tabloyu güncelle
            self.tablo.setRowCount(len(alt_klasorler) + 2)  # +2 for current directory files and total
            
            # Alt klasörleri ekle
            record_log(f"🗂️ Alt klasör sayısı: {len(alt_klasorler)}")  # Debug
            for satir, (klasor, boyut, dosya_sayisi) in enumerate(alt_klasorler):
                self.tablo_satiri_ekle(satir, klasor, boyut, dosya_sayisi)
            
            # Mevcut klasör dosyalarını ekle
            son_satir = len(alt_klasorler)
            self.tablo_satiri_ekle(
                son_satir,
                "Bu klasördeki dosyalar",
                mevcut_boyut,
                mevcut_dosya_sayisi,
                True
            )
            
            # Toplam satırını ekle
            toplam_satir = len(alt_klasorler) + 1
            self.tablo_satiri_ekle(
                toplam_satir,
                "TOPLAM",
                toplam_boyut,
                toplam_dosya,
                True,
                Qt.darkGray
            )
            
            # Kök dizinde miyiz kontrolü
            is_kok_dizin = (os.path.dirname(self.mevcut_klasor) == self.mevcut_klasor)
            self.ust_klasor_dugme.setEnabled(not is_kok_dizin)
        
        except PermissionError:
            QMessageBox.warning(self, "Hata", "Bu klasöre erişim izniniz yok!")
            self.ust_klasore_git()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Klasör analizi yapılırken hata oluştu: {str(e)}")

    def tablo_satiri_ekle(self, satir, isim, boyut, dosya_sayisi, arka_plan_rengi=False, renk=Qt.lightGray):
        """Tabloya yeni bir satır ekler"""
        # İsim
        isim_ogesi = QTableWidgetItem(isim)
        isim_ogesi.setFlags(isim_ogesi.flags() & ~Qt.ItemIsEditable)
        if arka_plan_rengi:
            isim_ogesi.setBackground(QColor(renk))  # QColor() ile sarmalayın
            font = isim_ogesi.font()
            font.setBold(True)
            isim_ogesi.setFont(font)
        self.tablo.setItem(satir, 0, isim_ogesi)
        
        # Boyut
        boyut_ogesi = QTableWidgetItem(self.boyut_formatla(boyut))
        boyut_ogesi.setFlags(boyut_ogesi.flags() & ~Qt.ItemIsEditable)
        boyut_ogesi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if arka_plan_rengi:
            boyut_ogesi.setBackground(QColor(renk))
            font = boyut_ogesi.font()
            font.setBold(True)
            boyut_ogesi.setFont(font)
        self.tablo.setItem(satir, 1, boyut_ogesi)
        
        # Dosya sayısı
        dosya_sayisi_ogesi = QTableWidgetItem(str(dosya_sayisi))
        dosya_sayisi_ogesi.setFlags(dosya_sayisi_ogesi.flags() & ~Qt.ItemIsEditable)
        dosya_sayisi_ogesi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if arka_plan_rengi:
            dosya_sayisi_ogesi.setBackground(QColor(renk))
            font = dosya_sayisi_ogesi.font()
            font.setBold(True)
            dosya_sayisi_ogesi.setFont(font)
        self.tablo.setItem(satir, 2, dosya_sayisi_ogesi)
