import os
import json
import datetime
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout, QAction, QMessageBox,
    QInputDialog, QDialog, QListWidget, QListWidgetItem, QGroupBox, QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer, Qt

MAX_DELETE_COUNT = 15  # Maksimum silme hakkı
MAX_SCORES_PER_DIFFICULTY = 15  # Her zorluk seviyesi için tutulacak maksimum skor
MAX_MISTAKES = 3  # Maksimum hata hakkı

class SudokuHucre:
    def __init__(self):
        self.deger = 0  # 0 boş hücreyi temsil eder
        self.sabit = False  # Başlangıçta verilen sayılar için
        self.notlar = set()  # Oyuncunun aldığı notlar

class SudokuOyunu(QMainWindow):
    # Renk tanımlamaları
    SABIT_RENK = "color: black; font-weight: bold;"
    KULLANICI_RENK = "color: #4169E1;"
    IPUCU_ARKAPLAN = "#2E8B57"  # Koyu yeşil (Sea Green)
    IPUCU_YAZI = "color: white; font-weight: bold;"
    HATA_ARKAPLAN = "#FFB6C1"  # Açık pembe (Light Pink)
    SECILI_ARKAPLAN = "#60EB60"  # Açık yeşil (Light Green)
    KULLANICI_ARKAPLAN = "#C4FF85"  # Açık yeşil-sarı
    NORMAL_ARKAPLAN = "white"
    VURGULU_ARKAPLAN = "#E8E8E8"  # Aynı satır/sütun/bölge için açık gri
    AYNI_SAYI_ARKAPLAN = "#FFD700"  # Aynı sayı için altın sarısı

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sudoku Profesyonel")
        self.resize(650, 720)
        
        # Oyun değişkenleri
        self.secili_hucre = None
        self.baslangic_zamani = None
        self.zorluk = "Kolay"  # Varsayılan zorluk
        self.puan = 0
        self.oyun_aktif = False
        self.cozum_tahtasi = None  # İpucu için çözüm tahtası
        self.hatali_hucreler = set()  # Hatalı hücreleri takip etmek için
        self.ipucu_hucreleri = set()  # İpucu hücrelerini takip etmek için
        
        # İstatistik değişkenleri
        self.ipucu_sayisi = 0
        self.silme_sayisi = 0
        self.kontrol_sayisi = 0
        self.hata_sayisi = 0  # Yanlış girilen sayı sayısı
        
        # Geri al/ileri al için geçmiş
        self.gecmis = []  # [(satir, sutun, eski_deger, yeni_deger), ...]
        self.gecmis_index = -1
        
        # Not modu
        self.not_modu = False
        self.notlar = [[set() for _ in range(9)] for _ in range(9)]  # Her hücre için notlar
        
        # Merkezi widget
        merkez_widget = QWidget()
        self.setCentralWidget(merkez_widget)
        ana_duzen = QVBoxLayout(merkez_widget)
        
        # Üst bilgi alanı - İlk satır
        ust_duzen = QHBoxLayout()
        
        # Zorluk seçici
        self.zorluk_combo = QComboBox()
        self.zorluk_combo.addItems(["Kolay", "Orta", "Zor"])
        self.zorluk_combo.currentTextChanged.connect(self.zorluk_degisti)
        ust_duzen.addWidget(QLabel("Zorluk:"))
        ust_duzen.addWidget(self.zorluk_combo)
        
        # Süre göstergesi
        self.sure_label = QLabel("Süre: 00:00")
        ust_duzen.addWidget(self.sure_label)
        
        # Puan göstergesi
        self.puan_label = QLabel("Puan: 0")
        ust_duzen.addWidget(self.puan_label)
        
        # Yeni değişkenler ekle
        self.silme_hakki = MAX_DELETE_COUNT
        self.toplam_puan = 0  # Toplam puan için yeni değişken
        self.oynanan_oyun_sayisi = 0  # Oynanan oyun sayısı
        
        # Toplam puan göstergesi
        self.toplam_puan_label = QLabel("Toplam Puan: 0")
        ust_duzen.addWidget(self.toplam_puan_label)
        
        # Sola hizalamak için stretch ekle
        ust_duzen.addStretch()
                
        ana_duzen.addLayout(ust_duzen)
        
        # İkinci satır - İstatistikler
        istatistik_duzen = QHBoxLayout()
        
        # Oyun sayısı göstergesi
        self.oyun_sayisi_label = QLabel("Oyun: 0")
        istatistik_duzen.addWidget(self.oyun_sayisi_label)

        # Silme hakkı göstergesi
        self.silme_hakki_label = QLabel(f"Silme Hakkı: {self.silme_hakki}")
        istatistik_duzen.addWidget(self.silme_hakki_label)
        
        # Hata sayısı göstergesi
        self.hata_label = QLabel(f"Hata: 0/{MAX_MISTAKES}")
        istatistik_duzen.addWidget(self.hata_label)
        
        # İpucu sayısı göstergesi
        self.ipucu_label = QLabel("İpucu: 0")
        istatistik_duzen.addWidget(self.ipucu_label)
        
        # Kontrol sayısı göstergesi
        self.kontrol_label = QLabel("Kontrol: 0")
        istatistik_duzen.addWidget(self.kontrol_label)
        
        # Not modu göstergesi
        self.not_modu_label = QLabel("Not: Kapalı")
        istatistik_duzen.addWidget(self.not_modu_label)
        
        # Sola hizalamak için stretch ekle
        istatistik_duzen.addStretch()
        
        ana_duzen.addLayout(istatistik_duzen)
        
        # Sudoku ızgarası
        self.izgara = QGridLayout()
        self.izgara.setSpacing(1)
        self.hucre_butonlari = []
        
        # 9x9 ızgarayı oluştur
        for i in range(9):
            satir = []
            for j in range(9):
                buton = QPushButton()
                buton.setFixedSize(50, 50)
                buton.setFont(QFont('Arial', 16))
                buton.clicked.connect(lambda checked, s=i, k=j: self.hucre_secildi(s, k))
                buton.setContextMenuPolicy(Qt.CustomContextMenu)
                buton.customContextMenuRequested.connect(lambda pos, s=i, k=j: self.sag_tus_menusu(s, k))
                self.izgara.addWidget(buton, i, j)
                satir.append(buton)
            self.hucre_butonlari.append(satir)
        
        # 3x3'lük bölgeleri belirginleştir
        for i in range(9):
            for j in range(9):
                self.hucre_butonlari[i][j].setStyleSheet("""
                    QPushButton {
                        background-color: white;
                        border: 1px solid gray;
                        margin: %dpx %dpx %dpx %dpx;
                    }
                """ % (
                    2 if i % 3 == 0 else 0,
                    2 if j % 3 == 0 else 0,
                    2 if i % 3 == 2 else 0,
                    2 if j % 3 == 2 else 0
                ))
        
        ana_duzen.addLayout(self.izgara)
        
        # Alt butonlar
        alt_duzen = QHBoxLayout()
        
        yeni_oyun_btn = QPushButton("Yeni Oyun")
        yeni_oyun_btn.clicked.connect(self.yeni_oyun)
        alt_duzen.addWidget(yeni_oyun_btn)
        
        kontrol_btn = QPushButton("Kontrol Et")
        kontrol_btn.clicked.connect(self.cozumu_kontrol_et)
        alt_duzen.addWidget(kontrol_btn)
        
        # İpucu butonu ekle
        ipucu_btn = QPushButton("İpucu")
        ipucu_btn.clicked.connect(self.ipucu_goster)
        alt_duzen.addWidget(ipucu_btn)
        
        # Oyunu Bitir butonu ekle
        bitir_btn = QPushButton("Oyunu Bitir")
        bitir_btn.clicked.connect(self.oyunu_bitir)
        alt_duzen.addWidget(bitir_btn)
        
        ana_duzen.addLayout(alt_duzen)
        
        # İkinci alt satır - Ek butonlar
        alt_duzen2 = QHBoxLayout()
        
        # Geri Al butonu
        geri_al_btn = QPushButton("↩ Geri Al")
        geri_al_btn.clicked.connect(self.geri_al)
        geri_al_btn.setToolTip("Son hamleyi geri al (Ctrl+Z)")
        alt_duzen2.addWidget(geri_al_btn)
        
        # İleri Al butonu
        ileri_al_btn = QPushButton("↪ İleri Al")
        ileri_al_btn.clicked.connect(self.ileri_al)
        ileri_al_btn.setToolTip("Geri alınan hamleyi tekrar yap (Ctrl+Y)")
        alt_duzen2.addWidget(ileri_al_btn)
        
        # Not Modu butonu
        self.not_modu_btn = QPushButton("📝 Not Modu")
        self.not_modu_btn.setCheckable(True)
        self.not_modu_btn.clicked.connect(self.not_modu_degistir)
        self.not_modu_btn.setToolTip("Not modu aç/kapat (N tuşu)")
        alt_duzen2.addWidget(self.not_modu_btn)
        
        # Notları Temizle butonu
        notlari_temizle_btn = QPushButton("🗑️ Notları Temizle")
        notlari_temizle_btn.clicked.connect(self.tum_notlari_temizle)
        alt_duzen2.addWidget(notlari_temizle_btn)
        
        ana_duzen.addLayout(alt_duzen2)
        
        # Menü oluştur
        self.menu_olustur()
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.sure_guncelle)
        
        # Oyun tahtası
        self.tahta = [[SudokuHucre() for _ in range(9)] for _ in range(9)]
        
        # Başlangıçta yeni oyun başlat
        self.yeni_oyun(puan_sifirla=True)
        
        # Klavye kısayolları için focus policy
        self.setFocusPolicy(Qt.StrongFocus)
    
    def menu_olustur(self):
        menubar = self.menuBar()
        
        # Oyun menüsü
        oyun_menu = menubar.addMenu('Oyun')
        
        yeni_oyun = QAction('Yeni Oyun', self)
        yeni_oyun.setShortcut('F2')
        yeni_oyun.triggered.connect(self.yeni_oyun)
        oyun_menu.addAction(yeni_oyun)
        
        puan_tablosu = QAction('Puan Tablosu', self)
        puan_tablosu.setShortcut('F3')
        puan_tablosu.triggered.connect(self.puan_tablosunu_goster)
        oyun_menu.addAction(puan_tablosu)
        
        oyunu_bitir = QAction('Oyunu Bitir', self)
        oyunu_bitir.setShortcut('F4')
        oyunu_bitir.triggered.connect(self.oyunu_bitir)
        oyun_menu.addAction(oyunu_bitir)
        
        # Yardım menüsü
        yardim_menu = menubar.addMenu('Yardım')
        
        nasil_oynanir = QAction('Nasıl Oynanır?', self)
        nasil_oynanir.triggered.connect(self.yardim_goster)
        yardim_menu.addAction(nasil_oynanir)
    
    def keyPressEvent(self, event):
        # Ctrl+Z: Geri al
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
            self.geri_al()
            return
        
        # Ctrl+Y: İleri al
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Y:
            self.ileri_al()
            return
        
        # N: Not modu aç/kapat
        if event.key() == Qt.Key_N:
            self.not_modu_degistir()
            return
        
        # Ok tuşları ile hücre hareketi
        if event.key() in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
            self.ok_tusu_hareketi(event.key())
            return
        
        if not self.secili_hucre or not self.oyun_aktif:
            return
        
        satir, sutun = self.secili_hucre
        
        if event.key() in [Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5,
                          Qt.Key_6, Qt.Key_7, Qt.Key_8, Qt.Key_9]:
            sayi = int(event.text())
            
            # Not modu aktifse nota ekle
            if self.not_modu:
                if not self.tahta[satir][sutun].sabit and self.tahta[satir][sutun].deger == 0:
                    if sayi in self.notlar[satir][sutun]:
                        self.notlar[satir][sutun].remove(sayi)
                    else:
                        self.notlar[satir][sutun].add(sayi)
                    self.hucreyi_guncelle(satir, sutun)
                return
            
            # Normal sayı girişi
            if not self.tahta[satir][sutun].sabit:
                eski_deger = self.tahta[satir][sutun].deger
                
                # Geçmişe kaydet (geri al için)
                self.gecmise_ekle(satir, sutun, eski_deger, sayi)
                
                self.tahta[satir][sutun].deger = sayi
                self.notlar[satir][sutun].clear()  # Sayı girilince notları temizle
                self.hucre_butonlari[satir][sutun].setText(str(sayi))
                
                # Anlık hata kontrolü - yanlış sayı girildiğinde
                if sayi != self.cozum_tahtasi[satir][sutun]:
                    self.hata_sayisi += 1
                    self.hata_label.setText(f"Hata: {self.hata_sayisi}/{MAX_MISTAKES}")
                    self.hatali_hucreler.add((satir, sutun))
                    
                    # Hata limitine ulaşıldıysa oyunu bitir
                    if self.hata_sayisi >= MAX_MISTAKES:
                        self.hucre_stilini_guncelle(satir, sutun)
                        self.oyun_bitti(f"Maksimum hata sayısına ({MAX_MISTAKES}) ulaştınız!")
                        return
                else:
                    # Doğru sayı girildiyse hatalı listesinden çıkar
                    if (satir, sutun) in self.hatali_hucreler:
                        self.hatali_hucreler.remove((satir, sutun))
                    # Aynı sayıyı içeren notları bölgeden temizle
                    self.ilgili_notlari_temizle(satir, sutun, sayi)
                
                self.hucre_stilini_guncelle(satir, sutun)
                
                # Tüm hücreler doluysa otomatik kontrol et
                self.otomatik_kontrol()
        
        elif event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # Hücreyi temizle
            if not self.tahta[satir][sutun].sabit and self.tahta[satir][sutun].deger != 0:
                if self.silme_hakki > 0:
                    eski_deger = self.tahta[satir][sutun].deger
                    self.gecmise_ekle(satir, sutun, eski_deger, 0)
                    
                    self.silme_hakki -= 1
                    self.silme_sayisi += 1  # Silme sayısını artır
                    self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
                    self.tahta[satir][sutun].deger = 0
                    self.hucre_butonlari[satir][sutun].setText("")
                    
                    # Hatalı hücreler listesinden kaldır
                    if (satir, sutun) in self.hatali_hucreler:
                        self.hatali_hucreler.remove((satir, sutun))
                    
                    self.hucre_stilini_guncelle(satir, sutun)
                    
                    # Silme hakkı bittiyse oyunu bitir
                    if self.silme_hakki == 0:
                        self.oyun_bitti("Silme hakkınız bitti!")
                else:
                    QMessageBox.warning(self, "Uyarı", "Silme hakkınız kalmadı!")
    
    def ok_tusu_hareketi(self, key):
        """Ok tuşları ile hücre hareketi"""
        if not self.secili_hucre:
            self.hucre_secildi(0, 0)
            return
        
        satir, sutun = self.secili_hucre
        
        if key == Qt.Key_Up and satir > 0:
            self.hucre_secildi(satir - 1, sutun)
        elif key == Qt.Key_Down and satir < 8:
            self.hucre_secildi(satir + 1, sutun)
        elif key == Qt.Key_Left and sutun > 0:
            self.hucre_secildi(satir, sutun - 1)
        elif key == Qt.Key_Right and sutun < 8:
            self.hucre_secildi(satir, sutun + 1)
    
    def gecmise_ekle(self, satir, sutun, eski_deger, yeni_deger):
        """Bir hamleyi geçmişe ekle"""
        # Eğer geri alınmış hamleler varsa, onları sil
        if self.gecmis_index < len(self.gecmis) - 1:
            self.gecmis = self.gecmis[:self.gecmis_index + 1]
        
        self.gecmis.append((satir, sutun, eski_deger, yeni_deger))
        self.gecmis_index = len(self.gecmis) - 1
    
    def geri_al(self):
        """Son hamleyi geri al"""
        if not self.oyun_aktif or self.gecmis_index < 0:
            return
        
        satir, sutun, eski_deger, yeni_deger = self.gecmis[self.gecmis_index]
        self.gecmis_index -= 1
        
        # Eski değeri geri yükle
        self.tahta[satir][sutun].deger = eski_deger
        if eski_deger == 0:
            self.hucre_butonlari[satir][sutun].setText("")
        else:
            self.hucre_butonlari[satir][sutun].setText(str(eski_deger))
        
        # Hatalı listesini güncelle
        if eski_deger == 0 or eski_deger == self.cozum_tahtasi[satir][sutun]:
            self.hatali_hucreler.discard((satir, sutun))
        elif eski_deger != self.cozum_tahtasi[satir][sutun]:
            self.hatali_hucreler.add((satir, sutun))
        
        self.hucre_stilini_guncelle(satir, sutun)
    
    def ileri_al(self):
        """Geri alınan hamleyi tekrar yap"""
        if not self.oyun_aktif or self.gecmis_index >= len(self.gecmis) - 1:
            return
        
        self.gecmis_index += 1
        satir, sutun, eski_deger, yeni_deger = self.gecmis[self.gecmis_index]
        
        # Yeni değeri uygula
        self.tahta[satir][sutun].deger = yeni_deger
        if yeni_deger == 0:
            self.hucre_butonlari[satir][sutun].setText("")
        else:
            self.hucre_butonlari[satir][sutun].setText(str(yeni_deger))
        
        # Hatalı listesini güncelle
        if yeni_deger == 0 or yeni_deger == self.cozum_tahtasi[satir][sutun]:
            self.hatali_hucreler.discard((satir, sutun))
        elif yeni_deger != self.cozum_tahtasi[satir][sutun]:
            self.hatali_hucreler.add((satir, sutun))
        
        self.hucre_stilini_guncelle(satir, sutun)
    
    def not_modu_degistir(self):
        """Not modunu aç/kapat"""
        self.not_modu = not self.not_modu
        self.not_modu_btn.setChecked(self.not_modu)
        self.not_modu_label.setText(f"Not: {'Açık' if self.not_modu else 'Kapalı'}")
    
    def tum_notlari_temizle(self):
        """Tüm notları temizle"""
        if not self.oyun_aktif:
            return
        
        for i in range(9):
            for j in range(9):
                self.notlar[i][j].clear()
                self.hucreyi_guncelle(i, j)
    
    def ilgili_notlari_temizle(self, satir, sutun, sayi):
        """Aynı satır, sütun ve 3x3 bölgedeki ilgili notları temizle"""
        # Aynı satır
        for j in range(9):
            self.notlar[satir][j].discard(sayi)
            self.hucreyi_guncelle(satir, j)
        
        # Aynı sütun
        for i in range(9):
            self.notlar[i][sutun].discard(sayi)
            self.hucreyi_guncelle(i, sutun)
        
        # Aynı 3x3 bölge
        kutu_satir = (satir // 3) * 3
        kutu_sutun = (sutun // 3) * 3
        for i in range(kutu_satir, kutu_satir + 3):
            for j in range(kutu_sutun, kutu_sutun + 3):
                self.notlar[i][j].discard(sayi)
                self.hucreyi_guncelle(i, j)
    
    def hucreyi_guncelle(self, satir, sutun):
        """Hücrenin içeriğini güncelle (sayı veya notlar)"""
        buton = self.hucre_butonlari[satir][sutun]
        hucre = self.tahta[satir][sutun]
        
        if hucre.deger != 0:
            buton.setText(str(hucre.deger))
            buton.setFont(QFont('Arial', 16))
        elif self.notlar[satir][sutun]:
            # Notları 3x3 grid formatında göster
            not_metni = ""
            for n in range(1, 10):
                if n in self.notlar[satir][sutun]:
                    not_metni += str(n)
                else:
                    not_metni += " "
                if n % 3 == 0 and n < 9:
                    not_metni += "\n"
            buton.setText(not_metni)
            buton.setFont(QFont('Arial', 8))
        else:
            buton.setText("")
            buton.setFont(QFont('Arial', 16))

    def otomatik_kontrol(self):
        """Tüm hücreler doluysa otomatik olarak kontrol et"""
        if not self.oyun_aktif:
            return
        
        # Tüm hücrelerin dolu olup olmadığını kontrol et
        for i in range(9):
            for j in range(9):
                if self.tahta[i][j].deger == 0:
                    return  # Boş hücre varsa kontrol yapma
        
        # Tüm hücreler doluysa kontrol et
        self.cozumu_kontrol_et()

    def hucre_secildi(self, satir, sutun):
        """Bir hücre seçildiğinde çağrılır"""
        # Önceki seçili hücre
        eski_secili = self.secili_hucre
        
        # Yeni hücreyi seç
        self.secili_hucre = (satir, sutun)
        
        # Tüm tahtayı yeniden stillendir (vurgulama için)
        self.tum_hucreleri_guncelle()
    
    def tum_hucreleri_guncelle(self):
        """Tüm hücrelerin stillerini güncelle (vurgulama için)"""
        for i in range(9):
            for j in range(9):
                secili = self.secili_hucre == (i, j)
                self.hucre_stilini_guncelle(i, j, secili=secili)
    
    def hucre_vurgulu_mu(self, satir, sutun):
        """Hücrenin vurgulanması gerekip gerekmediğini kontrol et"""
        if not self.secili_hucre:
            return False, False
        
        secili_satir, secili_sutun = self.secili_hucre
        secili_deger = self.tahta[secili_satir][secili_sutun].deger
        hucre_deger = self.tahta[satir][sutun].deger
        
        # Aynı sayı vurgusu
        ayni_sayi = secili_deger != 0 and hucre_deger == secili_deger and (satir, sutun) != self.secili_hucre
        
        # Aynı satır, sütun veya bölge vurgusu
        ayni_satir = satir == secili_satir
        ayni_sutun = sutun == secili_sutun
        ayni_bolge = (satir // 3 == secili_satir // 3) and (sutun // 3 == secili_sutun // 3)
        ilgili_hucre = (ayni_satir or ayni_sutun or ayni_bolge) and (satir, sutun) != self.secili_hucre
        
        return ayni_sayi, ilgili_hucre
    
    def hucre_stilini_guncelle(self, satir, sutun, secili=False):
        """Hücrenin stilini durumuna göre günceller"""
        buton = self.hucre_butonlari[satir][sutun]
        hucre = self.tahta[satir][sutun]
        
        # Margin değerlerini hesapla
        margin_top = 2 if satir % 3 == 0 else 0
        margin_left = 2 if sutun % 3 == 0 else 0
        margin_bottom = 2 if satir % 3 == 2 else 0
        margin_right = 2 if sutun % 3 == 2 else 0
        
        # Vurgulama kontrolü
        ayni_sayi, ilgili_hucre = self.hucre_vurgulu_mu(satir, sutun)
        
        # Öncelik sırası: İpucu > Hatalı > Seçili > Aynı Sayı > İlgili Hücre > Normal
        if (satir, sutun) in self.ipucu_hucreleri:
            # İpucu hücreleri - koyu yeşil arkaplan, beyaz yazı
            stil = f"""
                QPushButton {{
                    background-color: {self.IPUCU_ARKAPLAN};
                    {self.IPUCU_YAZI}
                    border: {'2px solid blue' if secili else '1px solid gray'};
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        elif (satir, sutun) in self.hatali_hucreler:
            # Hatalı hücreler - pembe arkaplan
            stil = f"""
                QPushButton {{
                    background-color: {self.HATA_ARKAPLAN};
                    {self.KULLANICI_RENK}
                    border: {'2px solid blue' if secili else '1px solid gray'};
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        elif secili:
            # Seçili hücre - açık yeşil arkaplan
            if hucre.sabit:
                renk = self.SABIT_RENK
            elif hucre.deger != 0:
                renk = self.KULLANICI_RENK
            else:
                renk = ""
            
            stil = f"""
                QPushButton {{
                    background-color: {self.SECILI_ARKAPLAN};
                    {renk}
                    border: 2px solid blue;
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        elif ayni_sayi:
            # Aynı sayıya sahip hücreler - altın sarısı arkaplan
            if hucre.sabit:
                renk = self.SABIT_RENK
            else:
                renk = self.KULLANICI_RENK
            
            stil = f"""
                QPushButton {{
                    background-color: {self.AYNI_SAYI_ARKAPLAN};
                    {renk}
                    border: 1px solid gray;
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        elif ilgili_hucre:
            # İlgili hücreler (aynı satır/sütun/bölge) - açık gri arkaplan
            if hucre.sabit:
                renk = self.SABIT_RENK
            elif hucre.deger != 0:
                renk = self.KULLANICI_RENK
            else:
                renk = ""
            
            stil = f"""
                QPushButton {{
                    background-color: {self.VURGULU_ARKAPLAN};
                    {renk}
                    border: 1px solid gray;
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        else:
            # Normal hücre
            if hucre.sabit:
                arkaplan = self.NORMAL_ARKAPLAN
                renk = self.SABIT_RENK
            elif hucre.deger != 0:
                arkaplan = self.KULLANICI_ARKAPLAN
                renk = self.KULLANICI_RENK
            else:
                arkaplan = self.NORMAL_ARKAPLAN
                renk = ""
            
            stil = f"""
                QPushButton {{
                    background-color: {arkaplan};
                    {renk}
                    border: 1px solid gray;
                    margin: {margin_top}px {margin_left}px {margin_bottom}px {margin_right}px;
                }}
            """
        
        buton.setStyleSheet(stil)
    
    def yeni_oyun(self, puan_sifirla=True):
        """Yeni oyun başlat"""
        # Zorluk seviyesini combobox'tan al - BU ÇOK ÖNEMLİ!
        self.zorluk = self.zorluk_combo.currentText()
        
        # Oyun tahtasını temizle
        for i in range(9):
            for j in range(9):
                self.tahta[i][j] = SudokuHucre()
                self.hucre_butonlari[i][j].setText("")
                self.hucre_butonlari[i][j].setFont(QFont('Arial', 16))
                self.hucre_butonlari[i][j].setStyleSheet(self.normal_hucre_stili(i, j))
        
        # Hata ve ipucu listelerini temizle
        self.hatali_hucreler.clear()
        self.ipucu_hucreleri.clear()
        
        # Notları temizle
        self.notlar = [[set() for _ in range(9)] for _ in range(9)]
        
        # Geçmişi temizle
        self.gecmis = []
        self.gecmis_index = -1
        
        # Yeni oyun ise İstatistikleri sıfırla
        if puan_sifirla:
            self.ipucu_sayisi = 0
            self.silme_sayisi = 0
            self.toplam_puan = 0
            self.hata_sayisi = 0

        self.kontrol_sayisi = 0
        self.oynanan_oyun_sayisi = 0
        
        # Yeni oyun oluştur
        self.tahta = self.sudoku_olustur(self.zorluk)
        
        # Tahtayı göster
        self.tahtayi_guncelle()
        
        # Süreyi başlat (15 dakika = 900 saniye)
        self.baslangic_zamani = datetime.datetime.now()
        self.kalan_sure = 900  # 15 dakika
        self.timer.start(1000)  # Her saniye güncelle
        self.oyun_aktif = True
        
        # Her zaman tüm değerleri sıfırla (Yeni Oyun butonu davranışı)
        self.puan = 500
        self.silme_hakki = MAX_DELETE_COUNT
        
        # Label'ları güncelle
        self.puan_label.setText(f"Puan: {self.puan}")
        self.toplam_puan_label.setText("Toplam Puan: 0")
        self.oyun_sayisi_label.setText("Oyun: 1")
        self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
        self.hata_label.setText(f"Hata: 0/{MAX_MISTAKES}")
        self.ipucu_label.setText("İpucu: " + str(self.ipucu_sayisi))
        self.kontrol_label.setText("Kontrol: 0")

    def sudoku_olustur(self, zorluk):
        """Sudoku tahtası oluştur ve çözümünü sakla"""
        tahta = [[SudokuHucre() for _ in range(9)] for _ in range(9)]
        
        # Yeni ve rastgele bir Sudoku tahtası oluştur
        bos_tahta = [[0 for _ in range(9)] for _ in range(9)]
        self.cozum_tahtasi = self.sudoku_coz(bos_tahta)  # Önce tam çözülmüş bir tahta oluştur
        
        # Zorluk seviyesine göre rakam sayısını belirle
        if zorluk == "Kolay":
            silinecek_sayi = 40  # 41 rakam görünür
        elif zorluk == "Orta":
            silinecek_sayi = 50  # 31 rakam görünür
        else:  # Zor
            silinecek_sayi = 60  # 21 rakam görünür
        
        # Rastgele hücreleri boşalt
        dolu_hucreler = [(i, j) for i in range(9) for j in range(9)]
        random.shuffle(dolu_hucreler)
        
        baslangic_tahtasi = [row[:] for row in self.cozum_tahtasi]
        for i, j in dolu_hucreler[:silinecek_sayi]:
            baslangic_tahtasi[i][j] = 0
        
        # Tahtayı ayarla
        for i in range(9):
            for j in range(9):
                tahta[i][j].deger = baslangic_tahtasi[i][j]
                if baslangic_tahtasi[i][j] != 0:
                    tahta[i][j].sabit = True
        
        return tahta
    
    def sudoku_coz(self, tahta):
        """Sudoku çözme algoritması"""
        bos = self.bos_hucre_bul(tahta)
        if not bos:
            return tahta
        
        satir, sutun = bos
        sayilar = list(range(1, 10))
        random.shuffle(sayilar)  # Rastgele çözüm için sayıları karıştır
        
        for sayi in sayilar:
            if self.sayi_uygun_mu(tahta, sayi, (satir, sutun)):
                tahta[satir][sutun] = sayi
                
                if self.sudoku_coz(tahta):
                    return tahta
                
                tahta[satir][sutun] = 0
        
        return False
    
    def bos_hucre_bul(self, tahta):
        """Boş hücre bul"""
        for i in range(9):
            for j in range(9):
                if tahta[i][j] == 0:
                    return (i, j)
        return None
    
    def sayi_uygun_mu(self, tahta, sayi, pos):
        """Sayının belirtilen konuma uygun olup olmadığını kontrol et"""
        # Satır kontrolü
        for j in range(9):
            if tahta[pos[0]][j] == sayi and pos[1] != j:
                return False
        
        # Sütun kontrolü
        for i in range(9):
            if tahta[i][pos[1]] == sayi and pos[0] != i:
                return False
        
        # 3x3 kutu kontrolü
        kutu_x = pos[1] // 3
        kutu_y = pos[0] // 3
        
        for i in range(kutu_y * 3, kutu_y * 3 + 3):
            for j in range(kutu_x * 3, kutu_x * 3 + 3):
                if tahta[i][j] == sayi and (i, j) != pos:
                    return False
        
        return True
    
    def tahtayi_guncelle(self):
        """Tahtayı görsel olarak güncelle"""
        for i in range(9):
            for j in range(9):
                hucre = self.tahta[i][j]
                buton = self.hucre_butonlari[i][j]
                
                if hucre.deger != 0:
                    buton.setText(str(hucre.deger))
                    if hucre.sabit:
                        # Başlangıçta verilen sayılar siyah renkte
                        buton.setStyleSheet("""
                            QPushButton {
                                background-color: white;
                                color: black;
                                font-weight: bold;
                                border: 1px solid gray;
                                margin: %dpx %dpx %dpx %dpx;
                            }
                        """ % (
                            2 if i % 3 == 0 else 0,
                            2 if j % 3 == 0 else 0,
                            2 if i % 3 == 2 else 0,
                            2 if j % 3 == 2 else 0
                        ))
                    else:
                        # Kullanıcının girdiği sayılar açık mavi
                        # MUSTAFA 13.11.2025
                        buton.setStyleSheet("""
                            QPushButton {
                                background-color: #C4FF85; 
                                color: #4169E1;  /* Royal Blue */
                                border: 1px solid gray;
                                margin: %dpx %dpx %dpx %dpx;
                            }
                        """ % (
                            2 if i % 3 == 0 else 0,
                            2 if j % 3 == 0 else 0,
                            2 if i % 3 == 2 else 0,
                            2 if j % 3 == 2 else 0
                        ))
                else:
                    buton.setText("")
                    buton.setStyleSheet("""
                        QPushButton {
                            background-color: white;
                            border: 1px solid gray;
                            margin: %dpx %dpx %dpx %dpx;
                        }
                    """ % (
                        2 if i % 3 == 0 else 0,
                        2 if j % 3 == 0 else 0,
                        2 if i % 3 == 2 else 0,
                        2 if j % 3 == 2 else 0
                    ))
    
    def sure_guncelle(self):
        if self.baslangic_zamani and self.oyun_aktif:
            gecen_sure = datetime.datetime.now() - self.baslangic_zamani
            dakika = gecen_sure.seconds // 60
            saniye = gecen_sure.seconds % 60
            self.sure_label.setText(f"Süre: {dakika:02d}:{saniye:02d}")
            
            # Her 30 saniyede bir puan düşür
            if gecen_sure.seconds > 0 and gecen_sure.seconds % 30 == 0:
                self.puan = max(0, self.puan - 1)  # Puan 0'ın altına düşmeyecek
                self.puan_label.setText(f"Puan: {self.puan}")
    
    def cozumu_kontrol_et(self):
        """Mevcut durumu kontrol et"""
        
        bos_hucre_var = False
        hatali_hucreler = []
        
        # Önce kullanıcının girdiği sayıları kontrol et
        for i in range(9):
            for j in range(9):
                if self.tahta[i][j].deger == 0:
                    bos_hucre_var = True
                elif not self.tahta[i][j].sabit:
                    if self.tahta[i][j].deger != self.cozum_tahtasi[i][j]:
                        hatali_hucreler.append((i, j))
        
        if hatali_hucreler:
            self.kontrol_sayisi += 1
            self.kontrol_label.setText(f"Kontrol: {self.kontrol_sayisi}")
            self.hatali_hucreler = set(hatali_hucreler)
            
            for satir, sutun in hatali_hucreler:
                self.hucre_stilini_guncelle(satir, sutun)
            
            hata_konumlari = ", ".join([f"({s+1},{k+1})" for s, k in hatali_hucreler])
            QMessageBox.warning(
                self, 
                "Bulunan Hatalı Sayılar", 
                f"Şu konumlardaki sayılar hatalı:\n{hata_konumlari}\n\n" +
                "(Hatalı hücreler pembe arka planla işaretlendi)"
            )
            return
        
        if bos_hucre_var:
            QMessageBox.information(self, "Kontrol", "Henüz tüm hücreler doldurulmamış!")
            return
        
        # Tüm hücreler dolu ve doğruysa
        self.oyun_aktif = False
        self.timer.stop()
        
        gecen_sure = int((datetime.datetime.now() - self.baslangic_zamani).total_seconds())
        self.toplam_puan += self.puan
        self.toplam_puan_label.setText(f"Toplam Puan: {self.toplam_puan}")
        
        # Oyun sayısını artır
        self.oynanan_oyun_sayisi += 1
        
        # Yeni oyun sorusu
        cevap = QMessageBox.question(
            self,
            "Tebrikler!",
            f"Sudoku'yu başarıyla çözdünüz!\n"
            f"Puan: {self.puan}\n"
            f"Toplam Puan: {self.toplam_puan}\n"
            f"Oynanan Oyun: {self.oynanan_oyun_sayisi}\n"
            f"Süre: {gecen_sure // 60:02d}:{gecen_sure % 60:02d}\n"
            f"İpucu: {self.ipucu_sayisi}, Silme: {self.silme_sayisi}, Kontrol: {self.kontrol_sayisi}\n\n"
            f"Yeni oyuna devam etmek ister misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if cevap == QMessageBox.Yes:
            # Devam ediyorsa skor tablosu kontrolü yapma
            self.silme_hakki = MAX_DELETE_COUNT
            self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
            # Devam oyunu için yeni tahta oluştur
            self.tahta = self.sudoku_olustur(self.zorluk)
            self.tahtayi_guncelle()
            self.hatali_hucreler.clear()
            self.ipucu_hucreleri.clear()
            self.notlar = [[set() for _ in range(9)] for _ in range(9)]
            self.gecmis = []
            self.gecmis_index = -1
            self.silme_sayisi = 0
            self.kontrol_sayisi = 0
            self.hata_sayisi = 0
            self.hata_label.setText(f"Hata: 0/{MAX_MISTAKES}")
            self.ipucu_label.setText("İpucu: "+ str(self.ipucu_sayisi))
            self.kontrol_label.setText("Kontrol: 0")
            self.puan = 500
            self.puan_label.setText(f"Puan: {self.puan}")
            self.oyun_sayisi_label.setText(f"Oyun: {self.oynanan_oyun_sayisi + 1}")
            self.baslangic_zamani = datetime.datetime.now()
            self.timer.start(1000)
            self.oyun_aktif = True
        else:
            # Devam etmiyorsa skor tablosu kontrolü yap
            skor_tablosuna_girebilir_mi = self.skor_tablosuna_girebilir_mi_kontrol(self.toplam_puan)
            
            if skor_tablosuna_girebilir_mi:
                isim, ok = QInputDialog.getText(
                    self, 
                    "Skor Tablosu", 
                    f"Skorunuz, puan tablosuna girmeye hak kazandı!\n"
                    f"Toplam Puan: {self.toplam_puan}\n"
                    f"Oynanan Oyun: {self.oynanan_oyun_sayisi}\n\n"
                    f"İsminizi girin:"
                )
                
                if ok and isim.strip():
                    self.puan_kaydet(isim.strip(), self.toplam_puan, gecen_sure)
            
            # Skor tablosunu göster (isim girilip girilmediğine bakmaksızın)
            self.puan_tablosunu_goster()

    def ipucu_goster(self):
        """Rastgele bir boş hücreye doğru sayıyı yerleştir. Mevcut puanı 10 puan azaltır"""
        if not self.oyun_aktif or not self.cozum_tahtasi:
            return
        
        if self.puan <= 10:
            QMessageBox.warning(self, "Uyarı", "Puanınız ipucu için yetersiz! (En az 10 puanınız olmalı)")
            return
        
        # Boş hücreleri bul
        bos_hucreler = []
        for i in range(9):
            for j in range(9):
                if self.tahta[i][j].deger == 0:
                    bos_hucreler.append((i, j))
        
        if not bos_hucreler:
            QMessageBox.information(self, "İpucu", "Tüm hücreler dolu!")
            return
        
        # Rastgele bir boş hücre seç
        satir, sutun = random.choice(bos_hucreler)
        
        # Doğru sayıyı yerleştir
        dogru_sayi = self.cozum_tahtasi[satir][sutun]
        self.tahta[satir][sutun].deger = dogru_sayi
        self.tahta[satir][sutun].sabit = True
        
        # İpucu hücresini kaydet ve sayacı artır
        self.ipucu_hucreleri.add((satir, sutun))
        self.ipucu_sayisi += 1
        self.ipucu_label.setText(f"İpucu: {self.ipucu_sayisi}")
        
        # Hücreyi güncelle
        buton = self.hucre_butonlari[satir][sutun]
        buton.setText(str(dogru_sayi))
        self.hucre_stilini_guncelle(satir, sutun)
        
        # Puanı güncelle
        self.puan = max(0, self.puan - 10)
        self.puan_label.setText(f"Puan: {self.puan}")

    def skor_tablosuna_girebilir_mi_kontrol(self, yeni_puan):
        """Yeni puanın skor tablosuna girip girmeyeceğini kontrol et"""
        try:
            puan_dosyasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_puanlar.json")
            
            puanlar = {"Kolay": [], "Orta": [], "Zor": []}
            if os.path.exists(puan_dosyasi):
                with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                    puanlar = json.load(f)
            
            zorluk_puanlari = puanlar.get(self.zorluk, [])
            
            # Eğer MAX_SCORES_PER_DIFFICULTY'den az kayıt varsa direkt girebilir
            if len(zorluk_puanlari) < MAX_SCORES_PER_DIFFICULTY:
                return True
            
            # En düşük skoru bul
            en_dusuk_skor = min(zorluk_puanlari, key=lambda x: x['puan'])
            
            # Yeni puan en düşük skordan yüksekse girebilir
            return yeni_puan > en_dusuk_skor['puan']
            
        except Exception:
            # Hata durumunda her zaman kaydetmeye izin ver
            return True

    def oyunu_bitir(self):
        """Oyunu bitir ve skor tablosu kontrolü yap"""
        if not self.oyun_aktif:
            QMessageBox.warning(self, "Uyarı", "Aktif oyun yok!")
            return
        
        # Kullanıcıya onay sor
        cevap = QMessageBox.question(
            self,
            "Oyunu Bitir",
            "Oyunu bitirmek istediğinizden emin misiniz?\n"
            "Mevcut ilerlemeniz kaybolacak!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if cevap != QMessageBox.Yes:
            return
        
        # Oyunu durdur
        self.oyun_aktif = False
        self.timer.stop()
        
        # Eğer hiç oyun tamamlanmadıysa (oynanan_oyun_sayisi == 0)
        if self.oynanan_oyun_sayisi == 0:
            QMessageBox.information(
                self,
                "Oyun Bitti",
                "Hiç oyun tamamlanmadığı için puan kaydedilmeyecek."
            )
            return
        
        # Mevcut toplam puan ile skor tablosu kontrolü
        gecen_sure = int((datetime.datetime.now() - self.baslangic_zamani).total_seconds())
        
        skor_tablosuna_girebilir_mi = self.skor_tablosuna_girebilir_mi_kontrol(self.toplam_puan)
        
        if skor_tablosuna_girebilir_mi:
            isim, ok = QInputDialog.getText(
                self, 
                "Skor Tablosu", 
                f"Skorunuz, puan tablosuna girmeye hak kazandı!\n"
                f"Toplam Puan: {self.toplam_puan}\n"
                f"Oynanan Oyun: {self.oynanan_oyun_sayisi}\n\n"
                f"İsminizi girin:"
            )
            
            if ok and isim.strip():
                self.puan_kaydet(isim.strip(), self.toplam_puan, gecen_sure)
        
        # Skor tablosunu göster
        self.puan_tablosunu_goster()

    def oyun_bitti(self, mesaj):
        """Silme hakkı bittiğinde oyunu bitir ve puan tablosuna girip girmediğini kontrol et"""
        self.oyun_aktif = False
        self.timer.stop()
        
        # Eğer hiç oyun tamamlanmadıysa
        if self.oynanan_oyun_sayisi == 0:
            QMessageBox.warning(self, "Oyun Bitti!", f"{mesaj}\nHiç oyun tamamlanmadığı için puan kaydedilmeyecek.")
            return
        
        gecen_sure = int((datetime.datetime.now() - self.baslangic_zamani).total_seconds())
        
        skor_tablosuna_girebilir_mi = self.skor_tablosuna_girebilir_mi_kontrol(self.toplam_puan)
        
        if skor_tablosuna_girebilir_mi:
            isim, ok = QInputDialog.getText(
                self, 
                "Oyun Bitti!", 
                f"{mesaj}\n"
                f"Toplam Puan: {self.toplam_puan}\n"
                f"Oynanan Oyun: {self.oynanan_oyun_sayisi}\n\n"
                f"Skorunuz puan tablosuna girmeye hak kazandı!\n"
                f"İsminizi girin:"
            )
            
            if ok and isim.strip():
                self.puan_kaydet(isim.strip(), self.toplam_puan, gecen_sure)
        else:
            QMessageBox.information(
                self,
                "Oyun Bitti!",
                f"{mesaj}\n"
                f"Toplam Puan: {self.toplam_puan}\n"
                f"Oynanan Oyun: {self.oynanan_oyun_sayisi}"
            )
        
        # Skor tablosunu göster
        self.puan_tablosunu_goster()

    def puan_kaydet(self, isim, puan, sure=None):
        """Puanı kaydet ve en iyi MAX_SCORES_PER_DIFFICULTY skoru tut"""
        puan_dosyasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                  "sudoku_puanlar.json")
        
        puanlar = {"Kolay": [], "Orta": [], "Zor": []}
        if os.path.exists(puan_dosyasi):
            with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                puanlar = json.load(f)
        
        # Süre belirtilmediyse hesapla
        if sure is None and self.baslangic_zamani:
            sure = int((datetime.datetime.now() - self.baslangic_zamani).total_seconds())
        elif sure is None:
            sure = 0
        
        # Yeni puanı ekle - self.zorluk kullanarak doğru zorluk seviyesine kaydet
        puanlar[self.zorluk].append({
            'isim': isim,
            'puan': puan,
            'sure': sure,
            'ipucu': self.ipucu_sayisi,
            'silme': self.silme_sayisi,
            'kontrol': self.kontrol_sayisi,
            'hata': self.hata_sayisi,
            'oyun_sayisi': self.oynanan_oyun_sayisi,
            'zorluk': self.zorluk,  # Zorluk seviyesini de kaydet
            'tarih': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # Puana göre sırala (yüksekten düşüğe, eşit puanlarda süreye göre küçükten büyüğe) ve en iyi 15'i al
        puanlar[self.zorluk] = sorted(
            puanlar[self.zorluk], 
            key=lambda x: (-x['puan'], x['sure'])
        )[:MAX_SCORES_PER_DIFFICULTY]
        
        # Puanları kaydet
        with open(puan_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(puanlar, f, ensure_ascii=False, indent=2)
    
    def normal_hucre_stili(self, satir, sutun):
        """Hücrenin temel stilini döndürür"""
        return (
            "QPushButton { "
            "background-color: white; "
            "border: 1px solid gray; "
            f"margin: {2 if satir % 3 == 0 else 0}px {2 if sutun % 3 == 0 else 0}px "
            f"{2 if satir % 3 == 2 else 0}px {2 if sutun % 3 == 2 else 0}px; "
            "padding: 0px; "
            "} "
        )
    
    def zorluk_degisti(self, yeni_zorluk):
        """Zorluk seviyesi değiştiğinde çağrılır"""
        # Ara oyunlardaysa (oynanan_oyun_sayisi > 0) zorluk değiştirmeyi engelle
        if self.oynanan_oyun_sayisi > 0 and self.oyun_aktif:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Ara oyunlarda zorluk seviyesi değiştirilemez!\nYeni oyuna başlayın."
            )
            # Sinyal döngüsüne girmemek için geçici olarak sinyal bağlantısını kes
            self.zorluk_combo.currentTextChanged.disconnect(self.zorluk_degisti)
            self.zorluk_combo.setCurrentText(self.zorluk)
            self.zorluk_combo.currentTextChanged.connect(self.zorluk_degisti)
            return
        
        if self.oyun_aktif:
            cevap = QMessageBox.question(
                self,
                "Yeni Oyun",
                "Aktif oyun var. Yeni oyun başlatmak istiyor musunuz?",
                QMessageBox.Yes | QMessageBox.No
            )
            if cevap == QMessageBox.Yes:
                self.zorluk = yeni_zorluk
                self.yeni_oyun(puan_sifirla=False)
            else:
                # Zorluk değişikliğini geri al (sinyal döngüsüne girmemek için)
                self.zorluk_combo.currentTextChanged.disconnect(self.zorluk_degisti)
                self.zorluk_combo.setCurrentText(self.zorluk)
                self.zorluk_combo.currentTextChanged.connect(self.zorluk_degisti)

    def puan_tablosunu_goster(self):
        """Puan tablosunu tablo formatında göster"""
        try:
            # Puan tablosu dosyası
            puan_dosyasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_puanlar.json")
            
            # Mevcut puanları yükle
            puanlar = {"Kolay": [], "Orta": [], "Zor": []}
            if os.path.exists(puan_dosyasi):
                with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                    puanlar = json.load(f)
            
            # Puan tablosu penceresi
            dialog = QDialog(self)
            dialog.setWindowTitle("Puan Tablosu")
            dialog.setModal(True)
            dialog.resize(1000, 1300)
            
            # Düzen
            duzen = QVBoxLayout()
            
            # Zorluk seviyeleri için tablolar
            for zorluk in ["Kolay", "Orta", "Zor"]:
                # Grup kutusu
                grup = QGroupBox(zorluk)
                grup_duzen = QVBoxLayout()
                
                # Tablo oluştur (8 sütun)
                tablo = QTableWidget()
                tablo.setColumnCount(8)
                tablo.setHorizontalHeaderLabels(["Tarih", "İsim", "Puan", "Süre", "Oyun", "İpucu", "Silme", "Kontrol"])
                tablo.setContextMenuPolicy(Qt.CustomContextMenu)
                tablo.customContextMenuRequested.connect(
                    lambda pos, z=zorluk, t=tablo: self.puan_tablosu_sag_tus_menusu(pos, z, t)
                )
                
                # Zorluk seviyesine göre puanları al ve sırala
                zorluk_puanlari = sorted(
                    puanlar.get(zorluk, []), 
                    key=lambda x: (-x['puan'], x['sure'])
                )[:MAX_SCORES_PER_DIFFICULTY]
                
                tablo.setRowCount(len(zorluk_puanlari))              
                
                # Tabloyu doldur
                for i, kayit in enumerate(zorluk_puanlari):
                    # Eski kayıtlarda eksik alanlar olabilir
                    ipucu = kayit.get('ipucu', 0)
                    silme = kayit.get('silme', 0)
                    kontrol = kayit.get('kontrol', 0)
                    oyun_sayisi = kayit.get('oyun_sayisi', 1)
                    tarih = kayit.get('tarih', 'Bilinmiyor')
                    
                    sure = kayit['sure']
                    dakika = sure // 60
                    saniye = sure % 60

                    if tarih != 'Bilinmiyor':
                        dt = datetime.datetime.strptime(tarih.strip(), "%Y-%m-%d %H:%M:%S")
                        tarih = dt.strftime("%d-%m-%Y  %H:%M")
                    # print(tarih)

                    tablo.setItem(i, 0, QTableWidgetItem(str(tarih)))
                    tablo.setItem(i, 1, QTableWidgetItem(kayit['isim']))

                    item = QTableWidgetItem(str(kayit['puan']))
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    tablo.setItem(i, 2, item)                    
                    
                    tablo.setItem(i, 3, QTableWidgetItem(f"{dakika:02d}:{saniye:02d}"))
                    tablo.setItem(i, 4, QTableWidgetItem(str(oyun_sayisi)))
                    tablo.setItem(i, 5, QTableWidgetItem(str(ipucu)))
                    tablo.setItem(i, 6, QTableWidgetItem(str(silme)))
                    tablo.setItem(i, 7, QTableWidgetItem(str(kontrol)))
                
                # Tablo doldurulduktan sonra satır yüksekliğini ayarla
                for i in range(tablo.rowCount()):
                    tablo.setRowHeight(i, 20)   

                tablo.setColumnWidth(0, 180)  # Tarih
                tablo.setColumnWidth(1, 180)  # İsim
                tablo.setColumnWidth(2, 80)   # Puan
                tablo.setColumnWidth(3, 80)   # Süre
                tablo.setColumnWidth(4, 60)   # Oyun
                tablo.setColumnWidth(5, 60)   # İpucu
                tablo.setColumnWidth(6, 60)   # Silme
                tablo.setColumnWidth(7, 70)   # Kontrol

                # Tablo ayarları
                tablo.setEditTriggers(QTableWidget.NoEditTriggers)
                tablo.setSelectionBehavior(QTableWidget.SelectRows)
                
                grup_duzen.addWidget(tablo)
                grup.setLayout(grup_duzen)
                duzen.addWidget(grup)
            
            # Kapat düğmesi
            kapat_btn = QPushButton("Kapat")
            kapat_btn.clicked.connect(dialog.close)
            duzen.addWidget(kapat_btn)
            
            dialog.setLayout(duzen)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Puan tablosu gösterilirken hata oluştu: {str(e)}")
    
    def puan_tablosu_sag_tus_menusu(self, pos, zorluk, tablo):
        """Puan tablosunda sağ tıklama menüsü"""
        secili_satirlar = tablo.selectionModel().selectedRows()
        if len(secili_satirlar) != 1:
            return  # Tam olarak bir satır seçili değilse menü açılmasın

        secili_satir = secili_satirlar[0].row()
        
        # Context menü oluştur
        menu = QMenu(self)
        sil_action = menu.addAction("Bu Puan Kaydını Sil")
        
        action = menu.exec_(tablo.viewport().mapToGlobal(pos))
        
        if action == sil_action:
            # Onay iste
            cevap = QMessageBox.question(
                self,
                "Silme Onayı",
                f"{secili_satir + 1}. sıradaki kaydı silmek istediğinizden emin misiniz?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if cevap == QMessageBox.Yes:
                self.puan_kaydi_sil(zorluk, secili_satir)
                # Tabloyu yenile
                tablo.parent().parent().close()  # Dialog'u kapat
                self.puan_tablosunu_goster()  # Yeniden aç
    
    def puan_kaydi_sil(self, zorluk, satir_index):
        """Puan tablosundan belirtilen kaydı sil"""
        try:
            puan_dosyasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_puanlar.json")
            
            puanlar = {"Kolay": [], "Orta": [], "Zor": []}
            if os.path.exists(puan_dosyasi):
                with open(puan_dosyasi, 'r', encoding='utf-8') as f:
                    puanlar = json.load(f)
            
            # Zorluk seviyesine göre puanları al ve sırala
            zorluk_puanlari = sorted(
                puanlar.get(zorluk, []), 
                key=lambda x: (-x['puan'], x['sure'])
            )
            
            # Belirtilen satırı sil
            if 0 <= satir_index < len(zorluk_puanlari):
                silinen = zorluk_puanlari.pop(satir_index)
                
                # Güncellenmiş listeyi kaydet
                puanlar[zorluk] = zorluk_puanlari
                
                with open(puan_dosyasi, 'w', encoding='utf-8') as f:
                    json.dump(puanlar, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(
                    self, 
                    "Başarılı", 
                    f"{silinen['isim']} kullanıcısının kaydı silindi."
                )
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Kayıt silinirken hata oluştu: {str(e)}")
    
    def yardim_goster(self):
        """Yardım mesajını göster"""
        yardim_metni = """
        <h2>Sudoku Nasıl Oynanır?</h2>
        <p>Sudoku, 9x9'luk bir ızgarada oynanan bir bulmaca oyunudur.</p>
        
        <h3>Kurallar:</h3>
        <ul>
            <li>Her satırda 1'den 9'a kadar olan sayılar birer kez kullanılmalıdır.</li>
            <li>Her sütunda 1'den 9'a kadar olan sayılar birer kez kullanılmalıdır.</li>
            <li>Her 3x3'lük bölgede 1'den 9'a kadar olan sayılar birer kez kullanılmalıdır.</li>
        </ul>
        
        <h3>Puan Sistemi:</h3>
        <ul>
            <li>Her oyun 500 puanla başlar</li>
            <li>Her 30 saniyede 1 puan düşer</li>
            <li>Her ipucu kullanımı 10 puan düşürür</li>
            <li>Oyuncunun 15 silme hakkı vardır</li>
            <li>3 hata hakkı vardır</li>
            <li>Silme veya hata hakkı biterse oyun sonlanır</li>
            <li>Başarılı oyun bitiminde puanlar toplanır ve yeni oyuna devam edilebilir</li>
        </ul>
        
        <h3>Klavye Kontrolleri:</h3>
        <ul>
            <li>1-9: Sayı girmek için (Not modu kapalıyken)</li>
            <li>1-9: Not almak için (Not modu açıkken)</li>
            <li>Delete/Backspace: Hücreyi silmek için</li>
            <li>N: Not modunu aç/kapat</li>
            <li>Ctrl+Z/Y: Geri/İleri al</li>
            <li>F2: Yeni oyun başlatmak için</li>
            <li>F3: Puan tablosu</li>
            <li>F4: Oyunu bitir</li>
        </ul>
        
        <h3>Fare Kontrolleri:</h3>
        <ul>
            <li>Sol tık: Hücre seçmek için</li>
            <li>Sağ tık: Olası sayıları görmek için</li>
        </ul>
        
        <h3>Özellikler:</h3>
        <ul>
            <li><b>Not Modu:</b> Bir hücreye birden fazla olası sayı yazabilirsiniz</li>
            <li><b>Geri Al/İleri Al:</b> Hamlelerinizi geri alabilir veya tekrar yapabilirsiniz</li>
            <li><b>Sayı Vurgulama:</b> Bir sayıya tıkladığınızda aynı sayılar vurgulanır</li>
            <li><b>Bölge Vurgulama:</b> Seçili hücrenin satırı, sütunu ve bölgesi vurgulanır</li>
        </ul>
        
        <h3>Renkler:</h3>
        <ul>
            <li><span style="color:black; font-weight:bold;">Siyah sayılar:</span> Başlangıçta verilen sabit sayılar</li>
            <li><span style="color:#4169E1;">Mavi sayılar:</span> Oyuncu tarafından girilen sayılar</li>
            <li><span style="background-color:#2E8B57; color:white;">Koyu yeşil:</span> İpucu ile doldurulan hücreler</li>
            <li><span style="background-color:#FFB6C1;">Pembe:</span> Hatalı sayılar</li>
            <li><span style="background-color:#60EB60;">Açık yeşil:</span> Seçili hücre</li>
            <li><span style="background-color:#FFD700;">Altın sarısı:</span> Aynı sayıya sahip hücreler</li>
            <li><span style="background-color:#E8E8E8;">Açık gri:</span> İlgili satır/sütun/bölge</li>
        </ul>
        """
        
        QMessageBox.information(self, "Nasıl Oynanır?", yardim_metni)
    
    def sag_tus_menusu(self, satir, sutun):
        """Oyun panelindeki Hücreye sağ tıklama ile olası sayıları gösteren menü"""
        if not self.oyun_aktif:
            return
        
        # Sabit hücrelere menü gösterme
        if self.tahta[satir][sutun].sabit:
            return
        
        # Olası sayıları hesapla
        olasi_sayilar = self.olasi_sayilari_bul(satir, sutun)
        
        if not olasi_sayilar:
            QMessageBox.information(self, "Bilgi", "Bu hücreye yerleştirilebilecek uygun sayı yok!")
            return
        
        # Context menü oluştur
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #4169E1;
                font-size: 14pt;
                font-weight: bold;
            }
            QMenu::item {
                padding: 8px 25px;
                color: #4169E1;
            }
            QMenu::item:selected {
                background-color: #90EE90;
            }
        """)
        
        # Her olası sayı için bir action ekle
        for sayi in sorted(olasi_sayilar):
            action = menu.addAction(str(sayi))
            action.triggered.connect(lambda checked, s=sayi: self.sayi_sec(satir, sutun, s))
        
        # Menüyü butonun konumunda göster
        buton = self.hucre_butonlari[satir][sutun]
        menu.exec_(buton.mapToGlobal(buton.rect().bottomLeft()))
    
    def olasi_sayilari_bul(self, satir, sutun):
        """Bir hücreye yerleştirilebilecek olası sayıları bul"""
        olasi_sayilar = set(range(1, 10))
        
        # Aynı satırdaki sayıları çıkar
        for j in range(9):
            if self.tahta[satir][j].deger != 0:
                olasi_sayilar.discard(self.tahta[satir][j].deger)
        
        # Aynı sütundaki sayıları çıkar
        for i in range(9):
            if self.tahta[i][sutun].deger != 0:
                olasi_sayilar.discard(self.tahta[i][sutun].deger)
        
        # Aynı 3x3 bölgedeki sayıları çıkar
        kutu_satir = (satir // 3) * 3
        kutu_sutun = (sutun // 3) * 3
        for i in range(kutu_satir, kutu_satir + 3):
            for j in range(kutu_sutun, kutu_sutun + 3):
                if self.tahta[i][j].deger != 0:
                    olasi_sayilar.discard(self.tahta[i][j].deger)
        
        return olasi_sayilar
    
    def sayi_sec(self, satir, sutun, sayi):
        """Menüden seçilen sayıyı hücreye yerleştir"""
        if not self.oyun_aktif or self.tahta[satir][sutun].sabit:
            return
        
        # Sayıyı yerleştir
        self.tahta[satir][sutun].deger = sayi
        self.hucre_butonlari[satir][sutun].setText(str(sayi))
        
        # Eğer hücre hatalı listesindeyse ve doğru sayı girildiyse hatayı temizle
        if (satir, sutun) in self.hatali_hucreler:
            if sayi == self.cozum_tahtasi[satir][sutun]:
                self.hatali_hucreler.remove((satir, sutun))
        
        # Hücreyi seç ve stilini güncelle
        self.secili_hucre = (satir, sutun)
        self.hucre_stilini_guncelle(satir, sutun, secili=True)
        
        # Tüm hücreler doluysa otomatik kontrol et
        self.otomatik_kontrol()

    # ---------------------------------
