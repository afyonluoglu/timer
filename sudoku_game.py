import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QGridLayout, QAction, QMessageBox,
    QInputDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer, Qt

from ti_sudoku_engine import (
    MAX_DELETE_COUNT, MAX_SCORES_PER_DIFFICULTY, MAX_MISTAKES,
    SudokuHucre, sudoku_olustur, sudoku_coz, bos_hucre_bul,
    sayi_uygun_mu, olasi_sayilari_bul
)
from ti_sudoku_dialogs import (
    skor_tablosuna_girebilir_mi_kontrol, puan_kaydet,
    puan_tablosunu_goster, puan_tablosu_sag_tus_menusu,
    puan_kaydi_sil, yardim_goster
)
from ti_sudoku_board import SudokuBoardMixin


class SudokuOyunu(SudokuBoardMixin, QMainWindow):
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
                self.notlar[satir][sutun].clear()
                self.hucre_butonlari[satir][sutun].setText(str(sayi))

                # Anlık hata kontrolü
                if sayi != self.cozum_tahtasi[satir][sutun]:
                    self.hata_sayisi += 1
                    self.hata_label.setText(f"Hata: {self.hata_sayisi}/{MAX_MISTAKES}")
                    self.hatali_hucreler.add((satir, sutun))

                    if self.hata_sayisi >= MAX_MISTAKES:
                        self.hucre_stilini_guncelle(satir, sutun)
                        self.oyun_bitti(f"Maksimum hata sayısına ({MAX_MISTAKES}) ulaştınız!")
                        return
                else:
                    if (satir, sutun) in self.hatali_hucreler:
                        self.hatali_hucreler.remove((satir, sutun))
                    self.ilgili_notlari_temizle(satir, sutun, sayi)

                self.hucre_stilini_guncelle(satir, sutun)
                self.otomatik_kontrol()

        elif event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            if not self.tahta[satir][sutun].sabit and self.tahta[satir][sutun].deger != 0:
                if self.silme_hakki > 0:
                    eski_deger = self.tahta[satir][sutun].deger
                    self.gecmise_ekle(satir, sutun, eski_deger, 0)

                    self.silme_hakki -= 1
                    self.silme_sayisi += 1
                    self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
                    self.tahta[satir][sutun].deger = 0
                    self.hucre_butonlari[satir][sutun].setText("")

                    if (satir, sutun) in self.hatali_hucreler:
                        self.hatali_hucreler.remove((satir, sutun))

                    self.hucre_stilini_guncelle(satir, sutun)

                    if self.silme_hakki == 0:
                        self.oyun_bitti("Silme hakkınız bitti!")
                else:
                    QMessageBox.warning(self, "Uyarı", "Silme hakkınız kalmadı!")

    def yeni_oyun(self, puan_sifirla=True):
        """Yeni oyun başlat"""
        self.zorluk = self.zorluk_combo.currentText()

        for i in range(9):
            for j in range(9):
                self.tahta[i][j] = SudokuHucre()
                self.hucre_butonlari[i][j].setText("")
                self.hucre_butonlari[i][j].setFont(QFont('Arial', 16))
                self.hucre_butonlari[i][j].setStyleSheet(self.normal_hucre_stili(i, j))

        self.hatali_hucreler.clear()
        self.ipucu_hucreleri.clear()
        self.notlar = [[set() for _ in range(9)] for _ in range(9)]
        self.gecmis = []
        self.gecmis_index = -1

        if puan_sifirla:
            self.ipucu_sayisi = 0
            self.silme_sayisi = 0
            self.toplam_puan = 0
            self.hata_sayisi = 0

        self.kontrol_sayisi = 0
        self.oynanan_oyun_sayisi = 0

        self.tahta = self.sudoku_olustur(self.zorluk)
        self.tahtayi_guncelle()

        self.baslangic_zamani = datetime.datetime.now()
        self.kalan_sure = 900
        self.timer.start(1000)
        self.oyun_aktif = True

        self.puan = 500
        self.silme_hakki = MAX_DELETE_COUNT

        self.puan_label.setText(f"Puan: {self.puan}")
        self.toplam_puan_label.setText("Toplam Puan: 0")
        self.oyun_sayisi_label.setText("Oyun: 1")
        self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
        self.hata_label.setText(f"Hata: 0/{MAX_MISTAKES}")
        self.ipucu_label.setText("İpucu: " + str(self.ipucu_sayisi))
        self.kontrol_label.setText("Kontrol: 0")

    def sudoku_olustur(self, zorluk):
        """Sudoku tahtası oluştur ve çözümünü sakla"""
        tahta, cozum = sudoku_olustur(zorluk)
        self.cozum_tahtasi = cozum
        return tahta

    def sudoku_coz(self, tahta):
        """Sudoku çözme algoritması"""
        return sudoku_coz(tahta)

    def bos_hucre_bul(self, tahta):
        """Boş hücre bul"""
        return bos_hucre_bul(tahta)

    def sayi_uygun_mu(self, tahta, sayi, pos):
        """Sayının belirtilen konuma uygun olup olmadığını kontrol et"""
        return sayi_uygun_mu(tahta, sayi, pos)

    def olasi_sayilari_bul(self, satir, sutun):
        """Bir hücreye yerleştirilebilecek olası sayıları bul"""
        return olasi_sayilari_bul(self.tahta, satir, sutun)

    def sure_guncelle(self):
        """Geçen süreyi ve puanı günceller"""
        if self.baslangic_zamani and self.oyun_aktif:
            gecen_sure = datetime.datetime.now() - self.baslangic_zamani
            dakika = gecen_sure.seconds // 60
            saniye = gecen_sure.seconds % 60
            self.sure_label.setText(f"Süre: {dakika:02d}:{saniye:02d}")

            if gecen_sure.seconds > 0 and gecen_sure.seconds % 30 == 0:
                self.puan = max(0, self.puan - 1)
                self.puan_label.setText(f"Puan: {self.puan}")

    def cozumu_kontrol_et(self):
        """Mevcut durumu kontrol et"""
        bos_hucre_var = False
        hatali_hucreler = []

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

        self.oyun_aktif = False
        self.timer.stop()

        gecen_sure = int((datetime.datetime.now() - self.baslangic_zamani).total_seconds())
        self.toplam_puan += self.puan
        self.toplam_puan_label.setText(f"Toplam Puan: {self.toplam_puan}")

        self.oynanan_oyun_sayisi += 1

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
            self.silme_hakki = MAX_DELETE_COUNT
            self.silme_hakki_label.setText(f"Silme Hakkı: {self.silme_hakki}")
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
            self.ipucu_label.setText("İpucu: " + str(self.ipucu_sayisi))
            self.kontrol_label.setText("Kontrol: 0")
            self.puan = 500
            self.puan_label.setText(f"Puan: {self.puan}")
            self.oyun_sayisi_label.setText(f"Oyun: {self.oynanan_oyun_sayisi + 1}")
            self.baslangic_zamani = datetime.datetime.now()
            self.timer.start(1000)
            self.oyun_aktif = True
        else:
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

            self.puan_tablosunu_goster()

    def skor_tablosuna_girebilir_mi_kontrol(self, yeni_puan):
        """Yeni puanın skor tablosuna girip girmeyeceğini kontrol et"""
        return skor_tablosuna_girebilir_mi_kontrol(self.zorluk, yeni_puan)

    def oyunu_bitir(self):
        """Oyunu bitir ve skor tablosu kontrolü yap"""
        if not self.oyun_aktif:
            QMessageBox.warning(self, "Uyarı", "Aktif oyun yok!")
            return

        cevap = QMessageBox.question(
            self,
            "Oyunu Bitir",
            "Oyunu bitirmek istediğinizden emin misiniz?\n"
            "Mevcut ilerlemeniz kaybolacak!",
            QMessageBox.Yes | QMessageBox.No
        )

        if cevap != QMessageBox.Yes:
            return

        self.oyun_aktif = False
        self.timer.stop()

        if self.oynanan_oyun_sayisi == 0:
            QMessageBox.information(
                self,
                "Oyun Bitti",
                "Hiç oyun tamamlanmadığı için puan kaydedilmeyecek."
            )
            return

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

        self.puan_tablosunu_goster()

    def oyun_bitti(self, mesaj):
        """Silme hakkı bittiğinde oyunu bitir ve puan tablosuna girip girmediğini kontrol et"""
        self.oyun_aktif = False
        self.timer.stop()

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

        self.puan_tablosunu_goster()

    def puan_kaydet(self, isim, puan, sure=None):
        """Puanı kaydet ve en iyi MAX_SCORES_PER_DIFFICULTY skoru tut"""
        if sure is None and self.baslangic_zamani:
            sure = int((datetime.datetime.now() - self.baslangic_zamani).total_seconds())
        elif sure is None:
            sure = 0

        puan_kaydet(
            self.zorluk, isim, puan, sure,
            self.ipucu_sayisi, self.silme_sayisi, self.kontrol_sayisi,
            self.hata_sayisi, self.oynanan_oyun_sayisi
        )

    def zorluk_degisti(self, yeni_zorluk):
        """Zorluk seviyesi değiştiğinde çağrılır"""
        if self.oynanan_oyun_sayisi > 0 and self.oyun_aktif:
            QMessageBox.warning(
                self,
                "Uyarı",
                "Ara oyunlarda zorluk seviyesi değiştirilemez!\nYeni oyuna başlayın."
            )
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
                self.zorluk_combo.currentTextChanged.disconnect(self.zorluk_degisti)
                self.zorluk_combo.setCurrentText(self.zorluk)
                self.zorluk_combo.currentTextChanged.connect(self.zorluk_degisti)

    def puan_tablosunu_goster(self):
        """Puan tablosunu tablo formatında göster"""
        puan_tablosunu_goster(self, self.puan_kaydi_sil)

    def puan_tablosu_sag_tus_menusu(self, pos, zorluk, tablo):
        """Puan tablosunda sağ tıklama menüsü"""
        puan_tablosu_sag_tus_menusu(self, pos, zorluk, tablo, self.puan_kaydi_sil)

    def puan_kaydi_sil(self, zorluk, satir_index):
        """Puan tablosundan belirtilen kaydı sil"""
        puan_kaydi_sil(self, zorluk, satir_index)

    def yardim_goster(self):
        """Yardım mesajını göster"""
        yardim_goster(self)
