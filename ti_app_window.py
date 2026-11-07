"""
DMAG Zamanlayıcı ana pencere menüsü ve pencereler arası koordinasyon modülü.
"""

import os
import sys
import importlib
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QMessageBox, QDialog, QVBoxLayout, QLabel
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from dialog_classes import YardimPenceresi
from timer_formatter import format_time
from timer_logger import view_filtered_logs, record_log, LOG_DOSYASI
from timer_helpers import show_toast
from timer_file_analyzer import DosyaAnaliziPenceresi
from sudoku_game import SudokuOyunu
from tetris_game import TetrisOyunu




class AnaUygulamaPenceresi(QMainWindow):
    """Uygulamanın ana pencere çerçevesi, üst menüleri ve pencere kapatma kontrolü."""

    def __init__(self, zamanlayici_widget=None):
        super().__init__()
        self.setWindowTitle("DMAG Zamanlayıcı")
        self.resize(1100, 1350)

        if zamanlayici_widget is not None:
            self.zamanlayici_widget = zamanlayici_widget
        else:
            main_mod = sys.modules.get('__main__')
            if main_mod and hasattr(main_mod, 'ZamanlayiciUygulamasi'):
                self.zamanlayici_widget = main_mod.ZamanlayiciUygulamasi()
            else:
                tm = importlib.import_module('ti_main')
                self.zamanlayici_widget = tm.ZamanlayiciUygulamasi()

        self.setCentralWidget(self.zamanlayici_widget)
        self.menu_olustur()

    def menu_olustur(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()

        # Zamanlayıcı menüsü
        zamanlayici_menu = menubar.addMenu('Zamanlayıcı')

        yeni_zamanlayici_eylem = QAction('Yeni Zamanlayıcı', self)
        yeni_zamanlayici_eylem.setShortcut('Ctrl+T')
        yeni_zamanlayici_eylem.triggered.connect(self.zamanlayici_widget.yeni_zamanlayici_baslat)
        zamanlayici_menu.addAction(yeni_zamanlayici_eylem)

        yeni_kronometre_eylem = QAction('Yeni Kronometre', self)
        yeni_kronometre_eylem.setShortcut('Ctrl+K')
        yeni_kronometre_eylem.triggered.connect(self.zamanlayici_widget.yeni_kronometre_baslat)
        zamanlayici_menu.addAction(yeni_kronometre_eylem)

        yeni_hatirlatici_eylem = QAction('Yeni Hatırlatıcı', self)
        yeni_hatirlatici_eylem.setShortcut('Ctrl+R')
        yeni_hatirlatici_eylem.triggered.connect(self.zamanlayici_widget.hatirlatici_manager.yeni_hatirlatici_ekle)
        zamanlayici_menu.addAction(yeni_hatirlatici_eylem)

        # Araçlar menüsü
        araclar_menu = menubar.addMenu('Araçlar')

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

        sudoku_eylem = QAction('Sudoku', self)
        sudoku_eylem.setShortcut('Ctrl+S')
        sudoku_eylem.triggered.connect(self.sudoku_ac)
        oyunlar_menu.addAction(sudoku_eylem)

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
        """Program hakkında penceresini gösterir."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Program Hakkında")
        layout = QVBoxLayout()
        label = QLabel()

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
        self.tetris_pencere = TetrisOyunu()
        self.tetris_pencere.show()

    def closeEvent(self, event):
        """Pencere kapatma olayı kontrolü"""
        aktif_kronometre_sayisi = len(self.zamanlayici_widget.aktif_kronometreler)
        if aktif_kronometre_sayisi > 0:
            kronometre_bilgileri = []
            for k in self.zamanlayici_widget.aktif_kronometreler:
                durum = "çalışıyor" if k.calisma_durumu else "duraklatılmış"
                kronometre_bilgileri.append(f"  • {k.isim}: {k.get_formatted_time()} ({durum})")

            kronometre_listesi = "\n".join(kronometre_bilgileri)

            cevap = QMessageBox.warning(
                self,
                "Aktif Kronometre Uyarısı",
                f"Aktif {aktif_kronometre_sayisi} adet kronometre var:\n\n{kronometre_listesi}\n\n"
                "Programı kapatmak istediğinizden emin misiniz?\n"
                "(Kronometreler kaydedilecek ve program tekrar açıldığında devam edecektir)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if cevap == QMessageBox.No:
                event.ignore()
                return

        for timer in self.zamanlayici_widget.aktif_zamanlayicilar:
            record_log(f"☑️ [KAPANIŞ] Timer {timer.id} - '{timer.temel_aciklama}': Kalan süre {format_time(timer.sure)} kaydediliyor")

        for krono in self.zamanlayici_widget.aktif_kronometreler:
            record_log(f"☑️ [KAPANIŞ] Kronometre '{krono.isim}': Geçen süre {krono.get_formatted_time()} kaydediliyor")

        self.zamanlayici_widget.helpers.ayarlari_kaydet()
        event.accept()
        record_log("--------------------P R O G R A M  K A P A T I L D I ------------------")
