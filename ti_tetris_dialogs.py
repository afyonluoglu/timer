# ti_tetris_dialogs.py
import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QTableWidget, QTableWidgetItem, QTextEdit)
from PyQt5.QtCore import Qt

# Dosya Yolları ve Sabitler
HIGH_SCORE_FILE = 'tetris_scores.json'

FONT_SIZE_TITLE = 24
FONT_SIZE_LARGE = 22
FONT_SIZE_MEDIUM = 18


class HighScoreManager:
    """Tetris yüksek skorlarını JSON dosyasında yöneten sınıf"""
    def __init__(self, filename=HIGH_SCORE_FILE):
        score_file = os.path.join(os.path.dirname(__file__), filename)
        self.filename = score_file
        self.scores = self.load_scores()
    
    def load_scores(self):
        """Skorları dosyadan yükle"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_scores(self):
        """Skorları dosyaya kaydet"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.scores, f, indent=2, ensure_ascii=False)
    
    def add_score(self, name, score, level, lines, play_time, date_time):
        """Yeni skor ekle"""
        self.scores.append({
            'name': name,
            'score': score,
            'level': level,
            'lines': lines,
            'play_time': play_time,
            'date': date_time
        })
        self.scores.sort(key=lambda x: x['score'], reverse=True)
        self.scores = self.scores[:10]
        self.save_scores()
    
    def is_high_score(self, score):
        """Skorun ilk 10'a girip girmediğini kontrol et"""
        if len(self.scores) < 10:
            return True
        return score > self.scores[-1]['score']


class HighScoreDialog(QDialog):
    """En yüksek skorlar tablosu diyalog penceresi"""
    def __init__(self, scores, parent=None):
        super().__init__(parent)
        self.setWindowTitle('🏆 En Yüksek Skorlar')
        self.setMinimumSize(850, 750)
        self.init_ui(scores)
    
    def init_ui(self, scores):
        """Arayüz bileşenlerini oluştur"""
        layout = QVBoxLayout()
        
        title = QLabel('🏆 EN YÜKSEK 10 SKOR')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f'font-size: {FONT_SIZE_TITLE}px; font-weight: bold; margin: 10px;')
        layout.addWidget(title)
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(['Sıra', 'İsim', 'Skor', 'Seviye', 'Süre', 'Tarih'])
        table.setRowCount(len(scores))
        
        # Tablo başlık stilini düzenle
        header = table.horizontalHeader()
        header.setStyleSheet(f'''
            QHeaderView::section {{
                background-color: #2a2a2a;
                color: white;
                padding: 8px;
                border: 1px solid #444;
                font-size: {FONT_SIZE_MEDIUM}px;
                font-weight: bold;
            }}
        ''')
        
        # Satır yüksekliğini artır
        table.verticalHeader().setDefaultSectionSize(40)
        
        for i, score in enumerate(scores):
            rank_item = QTableWidgetItem(f'#{i+1}')
            rank_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 0, rank_item)
            
            name_item = QTableWidgetItem(score['name'])
            name_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 1, name_item)
            
            score_item = QTableWidgetItem(str(score['score']))
            score_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 2, score_item)
            
            level_item = QTableWidgetItem(str(score['level']))
            level_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 3, level_item)
            
            time_item = QTableWidgetItem(score.get('play_time', '-'))
            time_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 4, time_item)
            
            date_item = QTableWidgetItem(score.get('date', '-'))
            date_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 5, date_item)
        
        # Sütun genişliklerini manuel ayarla
        table.setColumnWidth(0, 80)   # Sıra
        table.setColumnWidth(1, 150)  # İsim
        table.setColumnWidth(2, 120)  # Skor
        table.setColumnWidth(3, 100)  # Seviye
        table.setColumnWidth(4, 100)  # Süre
        table.setColumnWidth(5, 200)  # Tarih
        
        table.setStyleSheet(f'''
            QTableWidget {{
                font-size: {FONT_SIZE_MEDIUM}px;
                gridline-color: #444;
                background-color: #1a1a1a;
                color: white;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
        ''')
        
        layout.addWidget(table)
        
        close_btn = QPushButton('Kapat')
        close_btn.setStyleSheet(f'font-size: {FONT_SIZE_MEDIUM}px; padding: 10px;')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class HelpDialog(QDialog):
    """Tetris yardım ve kurallar penceresi"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('📖 Yardım - Oyun Kuralları')
        self.setMinimumSize(750, 800)
        self.init_ui()
    
    def init_ui(self):
        """Yardım içeriğini oluştur"""
        layout = QVBoxLayout()
        
        title = QLabel('📖 TETRİS PRO - OYUN KURALLARI VE KONTROLLER')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f'font-size: {FONT_SIZE_LARGE}px; font-weight: bold; margin: 10px;')
        layout.addWidget(title)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setStyleSheet(f'font-size: {FONT_SIZE_MEDIUM}px; line-height: 1.8;')
        help_text.setHtml("""
        <h2>🎮 OYUNUN AMACI</h2>
        <p>Yukarıdan düşen farklı şekillerdeki blokları yatay satırlar oluşturacak şekilde yerleştirin. 
        Tam dolu satırlar temizlenir ve puan kazanırsınız!</p>
        
        <h2>🕹️ KONTROLLER</h2>
        <ul>
            <li><b>← →</b> : Parçayı sola/sağa hareket ettir</li>
            <li><b>↑ / Z</b> : Parçayı döndür</li>
            <li><b>↓</b> : Hızlı düşüş (Soft Drop) - Her hücre için +1 puan</li>
            <li><b>SPACE</b> : Anında düşür (Hard Drop) - Her hücre için +2 puan</li>
            <li><b>H / C</b> : Parçayı sakla (Hold) - Her düşüşte bir kez kullanılabilir</li>
            <li><b>P</b> : Oyunu duraklat/devam ettir</li>
            <li><b>F1</b> : Bu yardım ekranını aç</li>
            <li><b>F2</b> : İnmekte olan parçayı değiştir (Rastgele yeni parça)</li>
            <li><b>F3</b> : Joker kullan (En alt satırı temizle)</li>
        </ul>
        
        <h2>💎 JOKER SİSTEMİ</h2>
        <p>Her 300 puan kazandığınızda 1 joker hakkı kazanırsınız. F3 tuşuna basarak joker kullanabilir 
        ve en alt satırı temizleyebilirsiniz. Maksimum 10 joker biriktirilebilir.</p>
        
        <h2>📊 SKORLAMA SİSTEMİ</h2>
        <ul>
            <li><b>1 Satır</b> : 100 × Seviye puanı</li>
            <li><b>2 Satır</b> : 300 × Seviye puanı</li>
            <li><b>3 Satır</b> : 500 × Seviye puanı</li>
            <li><b>4 Satır (TETRİS!)</b> : 800 × Seviye puanı</li>
        </ul>
        
        <h2>⚡ SEVİYE SİSTEMİ</h2>
        <p>Her 10 satır temizlediğinizde bir seviye atlarsınız. Seviye yükseldikçe parçalar daha hızlı düşer 
        ve kazandığınız puanlar artar!</p>
        
        <h2>👻 GÖLGE PARÇA</h2>
        <p>Mevcut parçanızın düşeceği konumu gösteren yarı saydam gölge, size en iyi yerleştirme 
        pozisyonunu gösterir.</p>
        
        <h2>🎯 İPUÇLARI</h2>
        <ul>
            <li>Mümkün olduğunca TETRİS (4 satır birden) yapmaya çalışın - En yüksek puan!</li>
            <li>Hold özelliğini stratejik kullanın - Uzun çubuk (I) parçasını saklayın</li>
            <li>Boşluk bırakmamaya dikkat edin</li>
            <li>Jokerlerinizi kritik anlarda kullanın</li>
            <li>F2 ile parça değiştirme özelliğini acil durumlarda kullanın</li>
        </ul>
        
        <p style='margin-top: 20px; text-align: center;'><b>İyi Eğlenceler! 🎮</b></p>
        """)
        layout.addWidget(help_text)
        
        close_btn = QPushButton('Kapat')
        close_btn.setStyleSheet(f'font-size: {FONT_SIZE_MEDIUM}px; padding: 10px;')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

