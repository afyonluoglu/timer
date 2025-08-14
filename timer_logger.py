import os
import logging
import datetime
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QComboBox, QPushButton, QTextEdit, QLineEdit, QLabel, QMessageBox)
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt, QPoint
# from PyQt5.QtWidgets import QMenu

# Mikrosaniye desteği için özel formatter sınıfı
class MicrosecondFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            # datetime kullanarak mikrosaniyeli format
            dt = datetime.datetime.fromtimestamp(record.created)
            return dt.strftime(datefmt)
        else:
            return super().formatTime(record, datefmt)

# Log dosyası yolunu oluştur
def setup_logging(log_file_path):
    """Initialize logging system with proper configuration"""
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file_path)
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Formatı oluştur
    formatter = MicrosecondFormatter(
        fmt='%(asctime)s: %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S.%f'
    )
    
    # Handlers ekle
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Record the first log entry
    logging.info("    ⏰###### (C) 2025 DMAG Zamanlayıcı Uygulaması #####⏰")


def record_log(mesaj, level='info'):
    """Log messages with specified level"""
    try:
        if level == 'debug':
            logging.debug(mesaj)
        elif level == 'warning':
            logging.warning(mesaj)
        elif level == 'error':
            logging.error(mesaj)
        elif level == 'critical':
            logging.critical(mesaj)
        else:  # Default to info
            logging.info(mesaj)
    except Exception as e:
        print(f"!!!!! Log kaydedilemedi: {e}")


class LogViewerDialog(QDialog):
    def center_window(self):
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.desktop().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def __init__(self, parent=None, log_file_path=None):
        super().__init__(parent)
        self.setWindowTitle("Log İzleme ve Düzenleme")
        self.resize(1600, 1400)
        self.log_file_path = log_file_path
        self.setup_ui()
        self.load_logs()
        self.center_window()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtreleme:"))
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentIndexChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.level_combo)
        
        # Sıralama seçenekleri
        filter_layout.addWidget(QLabel("Sıralama:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Alfabetik (A→Z)", "Alfabetik (Z→A)"])
        self.sort_combo.setCurrentText("Alfabetik (Z→A)")  # Varsayılan değer ayarla        
        self.sort_combo.currentIndexChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.sort_combo)

        # self.filter_btn = QPushButton("Filtre Uygula")
        # self.filter_btn.clicked.connect(self.apply_filter)
        # filter_layout.addWidget(self.filter_btn)
        
        # Kelime arama özelliği 
        filter_layout.addWidget(QLabel("Arama:"))
        self.search_text = QLineEdit()
        self.search_text.setPlaceholderText("Aranacak kelime... (Kelimeler arasına AND ve OR için  + ve - koyun - Örnek:  zamanlayıcı+tamamlandı-toplantı)")
        self.search_text.returnPressed.connect(self.apply_filter)
        filter_layout.addWidget(self.search_text)

        self.search_text.setContextMenuPolicy(Qt.CustomContextMenu)
        self.search_text.customContextMenuRequested.connect(self.show_search_context_menu)

        self.search_btn = QPushButton("Ara")
        self.search_btn.clicked.connect(self.apply_filter)
        filter_layout.addWidget(self.search_btn)

        self.clear_btn = QPushButton("Temizle")
        self.clear_btn.clicked.connect(self.clear_search)
        filter_layout.addWidget(self.clear_btn)        

        layout.addLayout(filter_layout)
        
        # Log display
        self.log_text = QTextEdit()
        
        self.log_text.setFont(QFont("Courier New", 10))
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)

        layout.addWidget(self.log_text)
        
        # Kaydet ve Kapat düğmeleri
        button_layout = QHBoxLayout()
        button_layout.addStretch() # Düğmeleri sağa yasla

        self.save_button = QPushButton("Değişiklikleri Kaydet (Ctrl+S)")
        self.save_button.clicked.connect(self.save_logs)
        button_layout.addWidget(self.save_button)

        # Ctrl+S kısayolu ekle
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_logs)

        self.close_button = QPushButton("Kapat")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def show_search_context_menu(self, pos: QPoint):
        menu = self.search_text.createStandardContextMenu()
        menu.addSeparator()
        # menu.addAction("AND için + ekle", lambda: self.search_text.insert("+"))
        # menu.addAction("NOT için - ekle", lambda: self.search_text.insert("-"))
        menu.addAction("Favori Aramalara Ekle", self.add_search_to_favorites)

        # Favoriler alt menüsü
        favorites_menu = menu.addMenu("Favoriler")
        # Favori arama dosyasını oku
        log_dir = os.path.dirname(self.log_file_path) if self.log_file_path else os.getcwd()
        fav_file = os.path.join(log_dir, "log_favori_search.txt")
        favorites = []
        if os.path.exists(fav_file):
            try:
                with open(fav_file, "r", encoding="utf-8") as f:
                    favorites = [line.strip() for line in f if line.strip()]
            except Exception:
                favorites = []
        # Sadece ilk 10 favori göster
        for fav in favorites[:10]:
            favorites_menu.addAction(fav, lambda fav_text=fav: self.select_favorite_search(fav_text))
        if not favorites:
            favorites_menu.addAction("(Favori yok)").setEnabled(False)

        menu.exec_(self.search_text.mapToGlobal(pos))

    def select_favorite_search(self, fav_text):
        self.search_text.setText(fav_text)
        self.apply_filter()

    def add_search_to_favorites(self):
        """Arama kutusundaki metni log_favori_search.txt dosyasına ekler."""
        search_term = self.search_text.text().strip()
        if not search_term:
            QMessageBox.information(self, "Bilgi", "Favorilere eklemek için önce bir arama metni girin.")
            return
        try:
            # Favori arama dosyasının yolunu belirle (log dosyası ile aynı klasörde)
            log_dir = os.path.dirname(self.log_file_path) if self.log_file_path else os.getcwd()
            fav_file = os.path.join(log_dir, "log_favori_search.txt")
            with open(fav_file, "a", encoding="utf-8") as f:
                f.write(search_term + "\n")
            QMessageBox.information(self, "Başarılı", f"Arama favorilere eklendi:\n{search_term}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Favori arama kaydedilemedi:\n{e}")

    def save_logs(self):
        """QTextEdit içindeki mevcut içeriği log dosyasına kaydeder."""
        try:
            content = self.log_text.toPlainText()
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.all_logs = content.splitlines(True)
            QMessageBox.information(self, "Başarılı", "Log dosyası başarıyla kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Log dosyası kaydedilemedi:\n{str(e)}")
    
    def load_logs(self):
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                self.all_logs = f.readlines()
            # print(f"  [DEBUG] Loaded {len(self.all_logs)} lines from log file.")
            self.apply_filter()
        except Exception as e:
            self.log_text.setText(f"Error loading log file: {str(e)}")
    
    def clear_search(self):
        """Arama alanını temizler ve filtreleri uygular."""
        self.search_text.clear()
        self.apply_filter()

    def apply_filter(self):
        def turkish_lower(text):
            """Türkçe karakterler için doğru küçük harfe çevirme"""
            replacements = {
                'I': 'ı',
                'İ': 'i',
                'Ç': 'ç',
                'Ğ': 'ğ',
                'Ö': 'ö',
                'Ş': 'ş',
                'Ü': 'ü',
            }
            # Önce büyük Türkçe harfleri değiştir
            for k, v in replacements.items():
                text = text.replace(k, v)
            # Sonra normal lower uygula
            return text.lower()
        
        level = self.level_combo.currentText()
        search_term = turkish_lower(self.search_text.text().strip())
        # print(f"Applying filter: Level={level}, Search Term= {self.search_text.text()} --> '{search_term}'")
        sort_option = self.sort_combo.currentText()
        
        # Önce seviye filtresi uygula
        if level == "ALL":
            filtered_logs = self.all_logs.copy()
        else:
            filtered_logs = [line for line in self.all_logs if f": {level}:" in line]
        
        # Sonra arama terimini uygula (eğer varsa)
        if search_term:
                        # Hem + hem - varsa
            if '+' in search_term or '-' in search_term:
                # Önce NOT kelimelerini ayır
                not_split = search_term.split('-')
                and_part = not_split[0]
                not_words = []
                if len(not_split) > 1:
                    # NOT kelimeleri: '-' ile ayrılan ve + ile birleştirilenler
                    not_words = [w.strip() for w in '-'.join(not_split[1:]).split('+') if w.strip()]
                # AND kelimeleri: ilk '-' öncesi + ile ayrılanlar
                and_words = [w.strip() for w in and_part.split('+') if w.strip()]
                print(f"  [DEBUG] AND araması için kelimeler: {and_words}")
                print(f"  [DEBUG] NOT araması için kelimeler: {not_words}")
                # Filtreleme
                filtered_logs = [
                    line for line in filtered_logs
                    if all(word in turkish_lower(line.strip()) for word in and_words)
                    and all(word not in turkish_lower(line.strip()) for word in not_words)
                ]
            else:
                # Sadece tek kelime araması
                filtered_logs = [line for line in filtered_logs if search_term in turkish_lower(line.strip())]

        # Sıralama uygula
        if sort_option == "Alfabetik (A→Z)":
            filtered_logs.sort()
        elif sort_option == "Alfabetik (Z→A)":
            filtered_logs.sort(reverse=True)
        
        self.log_text.setText("".join(filtered_logs))
        self.setWindowTitle( f"Log İzleme ve Düzenleme - {len(filtered_logs)} kayıt görüntüleniyor")


def view_filtered_logs(log_file_path):
    """Open a window to view and filter log files"""
    dialog = LogViewerDialog(None, log_file_path)
    dialog.exec_()

if __name__ == "__main__":
    print("\n")
    print("        ##########################################################################################")
    print("        ⚠️  Uyarı: timer_logger.py doğrudan çalıştırıldı. Bu dosya TIMER projesinin LOG modülüdür.")    
    print("        ##########################################################################################")
    print("\n")

