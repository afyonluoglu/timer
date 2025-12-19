"""
TETRIS PRO - Gelişmiş Tetris Oyunu

Gerekli Kütüphaneler:
- PyQt5: pip install PyQt5
- json: Python standart kütüphanesi (ek kurulum gerektirmez)
- os: Python standart kütüphanesi (ek kurulum gerektirmez)
- random: Python standart kütüphanesi (ek kurulum gerektirmez)
- datetime: Python standart kütüphanesi (ek kurulum gerektirmez)
- time: Python standart kütüphanesi (ek kurulum gerektirmez)

Kurulum:
pip install PyQt5
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QInputDialog, QMessageBox,
                             QDialog, QTableWidget, QTableWidgetItem, QTextEdit, QApplication)
from PyQt5.QtCore import Qt, QTimer, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
import random
import json
import os
from datetime import datetime
import time

# ============================================================================
# OYUN SABİTLERİ VE YAPILANDIRMA
# ============================================================================

# Tahta Boyutları
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# Hız Ayarları (milisaniye)
INITIAL_SPEED = 1000
MIN_SPEED = 100
SPEED_DECREASE_PER_LEVEL = 50

# Skorlama
SCORE_SINGLE_LINE = 100
SCORE_DOUBLE_LINE = 300
SCORE_TRIPLE_LINE = 500
SCORE_TETRIS = 800
SOFT_DROP_POINTS = 1
HARD_DROP_POINTS = 2

# Seviye Sistemi
LINES_PER_LEVEL = 10

# Joker Sistemi
POINTS_PER_JOKER = 300
MAX_JOKERS = 10

# Font Boyutları
FONT_SIZE_TITLE = 24
FONT_SIZE_LARGE = 22
FONT_SIZE_MEDIUM = 18
FONT_SIZE_SMALL = 16
FONT_SIZE_CONTROLS = 14

# Renkler (Parlak/Neon Renkler)
COLOR_I = QColor(0, 255, 255)      # Cyan - Parlak
COLOR_O = QColor(255, 255, 0)      # Sarı - Parlak
COLOR_T = QColor(200, 0, 255)      # Mor - Parlak
COLOR_S = QColor(0, 255, 0)        # Yeşil - Parlak
COLOR_Z = QColor(255, 0, 0)        # Kırmızı - Parlak
COLOR_J = QColor(0, 100, 255)      # Mavi - Parlak
COLOR_L = QColor(255, 165, 0)      # Turuncu - Parlak

# Dosya Yolları
HIGH_SCORE_FILE = 'tetris_scores.json'

# ============================================================================
# TETROMINO TANIMLARI
# ============================================================================

TETROMINOS = {
    'I': {'shape': [[1, 1, 1, 1]], 'color': COLOR_I},
    'O': {'shape': [[1, 1], [1, 1]], 'color': COLOR_O},
    'T': {'shape': [[0, 1, 0], [1, 1, 1]], 'color': COLOR_T},
    'S': {'shape': [[0, 1, 1], [1, 1, 0]], 'color': COLOR_S},
    'Z': {'shape': [[1, 1, 0], [0, 1, 1]], 'color': COLOR_Z},
    'J': {'shape': [[1, 0, 0], [1, 1, 1]], 'color': COLOR_J},
    'L': {'shape': [[0, 0, 1], [1, 1, 1]], 'color': COLOR_L}
}

# ============================================================================
# YÜKSEK SKOR YÖNETİCİSİ
# ============================================================================

class HighScoreManager:
    def __init__(self, filename=HIGH_SCORE_FILE):
        score_file = os.path.join(os.path.dirname(__file__), filename)
        self.filename = score_file
        # print(f"Yüksek skor dosyası: {self.filename}")
        self.scores = self.load_scores()
    
    def load_scores(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_scores(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.scores, f, indent=2, ensure_ascii=False)
    
    def add_score(self, name, score, level, lines, play_time, date_time):
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
        if len(self.scores) < 10:
            return True
        return score > self.scores[-1]['score']

# ============================================================================
# YÜKSEK SKOR DİYALOĞU
# ============================================================================

class HighScoreDialog(QDialog):
    def __init__(self, scores, parent=None):
        super().__init__(parent)
        self.setWindowTitle('🏆 En Yüksek Skorlar')
        self.setMinimumSize(850, 750)
        self.init_ui(scores)
    
    def init_ui(self, scores):
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

# ============================================================================
# YARDIM DİYALOĞU
# ============================================================================

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('📖 Yardım - Oyun Kuralları')
        self.setMinimumSize(750, 800)
        self.init_ui()
    
    def init_ui(self):
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

# ============================================================================
# TETRİS OYUN TAHTASI
# ============================================================================

class TetrisBoard(QFrame):
    scoreChanged = pyqtSignal(int)
    levelChanged = pyqtSignal(int)
    linesChanged = pyqtSignal(int)
    jokersChanged = pyqtSignal(int)
    nextPieceChanged = pyqtSignal(str)
    holdPieceChanged = pyqtSignal(str)
    gameOver = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__(parent)
        self.timer = QBasicTimer()
        self.start_time = None
        self.init_board()
        
    def init_board(self):
        self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        self.next_piece_type = None
        self.hold_piece_type = None
        self.can_hold = True
        
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.jokers = 0
        self.last_joker_score = 0
        self.is_paused = False
        self.is_game_over = False
        self.start_time = time.time()
        
        self.setFocusPolicy(Qt.StrongFocus)
        self.spawn_new_piece()
        self.spawn_next_piece()
        
    def start(self):
        if self.is_game_over:
            self.init_board()
        self.timer.start(INITIAL_SPEED, self)
        
    def pause(self):
        if not self.is_game_over:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.timer.stop()
            else:
                self.timer.start(max(MIN_SPEED, INITIAL_SPEED - (self.level - 1) * SPEED_DECREASE_PER_LEVEL), self)
            self.update()
    
    def spawn_next_piece(self):
        self.next_piece_type = random.choice(list(TETROMINOS.keys()))
        self.nextPieceChanged.emit(self.next_piece_type)
    
    def spawn_new_piece(self):
        if self.next_piece_type is None:
            self.spawn_next_piece()
        
        self.current_piece_type = self.next_piece_type
        self.current_piece = [row[:] for row in TETROMINOS[self.current_piece_type]['shape']]
        self.current_x = BOARD_WIDTH // 2 - len(self.current_piece[0]) // 2
        self.current_y = 0
        self.can_hold = True
        
        self.spawn_next_piece()
        
        if not self.is_valid_position(self.current_piece, self.current_x, self.current_y):
            self.game_over_action()
    
    def change_current_piece(self):
        """F2 ile mevcut parçayı değiştir"""
        if self.is_paused or self.is_game_over:
            return
        
        new_type = random.choice(list(TETROMINOS.keys()))
        self.current_piece_type = new_type
        self.current_piece = [row[:] for row in TETROMINOS[new_type]['shape']]
        self.current_x = BOARD_WIDTH // 2 - len(self.current_piece[0]) // 2
        
        if not self.is_valid_position(self.current_piece, self.current_x, self.current_y):
            self.current_y = 0
        
        self.update()
    
    def use_joker(self):
        """F3 ile joker kullan - en alt satırı temizle"""
        if self.is_paused or self.is_game_over or self.jokers <= 0:
            return
        
        # En alt satırı temizle
        if any(self.board[BOARD_HEIGHT - 1]):
            del self.board[BOARD_HEIGHT - 1]
            self.board.insert(0, [None for _ in range(BOARD_WIDTH)])
            self.jokers -= 1
            self.jokersChanged.emit(self.jokers)
            self.update()
    
    def check_joker_earn(self):
        """Her 300 puanda joker kazan"""
        if self.score // POINTS_PER_JOKER > self.last_joker_score // POINTS_PER_JOKER:
            if self.jokers < MAX_JOKERS:
                self.jokers += 1
                self.jokersChanged.emit(self.jokers)
            self.last_joker_score = self.score
    
    def is_valid_position(self, piece, x, y):
        for row_idx, row in enumerate(piece):
            for col_idx, cell in enumerate(row):
                if cell:
                    new_x = x + col_idx
                    new_y = y + row_idx
                    if (new_x < 0 or new_x >= BOARD_WIDTH or 
                        new_y >= BOARD_HEIGHT or
                        (new_y >= 0 and self.board[new_y][new_x] is not None)):
                        return False
        return True
    
    def rotate_piece(self):
        if self.is_paused or self.is_game_over:
            return
        
        rotated = [list(row) for row in zip(*self.current_piece[::-1])]
        
        kick_offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1)]
        for dx, dy in kick_offsets:
            if self.is_valid_position(rotated, self.current_x + dx, self.current_y + dy):
                self.current_piece = rotated
                self.current_x += dx
                self.current_y += dy
                self.update()
                return
    
    def move_piece(self, dx):
        if self.is_paused or self.is_game_over:
            return
        
        if self.is_valid_position(self.current_piece, self.current_x + dx, self.current_y):
            self.current_x += dx
            self.update()
    
    def soft_drop(self):
        if self.is_paused or self.is_game_over:
            return
        
        if self.is_valid_position(self.current_piece, self.current_x, self.current_y + 1):
            self.current_y += 1
            self.score += SOFT_DROP_POINTS
            self.scoreChanged.emit(self.score)
            self.check_joker_earn()
            self.update()
    
    def hard_drop(self):
        if self.is_paused or self.is_game_over:
            return
        
        # Oyun başlamış mı kontrol et (timer çalışıyor mu?)
        if not self.timer.isActive():
            return
        
        drop_distance = 0
        while self.is_valid_position(self.current_piece, self.current_x, self.current_y + 1):
            self.current_y += 1
            drop_distance += 1
        
        self.score += drop_distance * HARD_DROP_POINTS
        self.scoreChanged.emit(self.score)
        self.check_joker_earn()
        self.lock_piece()
    
    def hold_piece(self):
        if self.is_paused or self.is_game_over or not self.can_hold:
            return
        
        if self.hold_piece_type is None:
            self.hold_piece_type = self.current_piece_type
            self.holdPieceChanged.emit(self.hold_piece_type)
            self.spawn_new_piece()
        else:
            self.hold_piece_type, self.current_piece_type = self.current_piece_type, self.hold_piece_type
            self.current_piece = [row[:] for row in TETROMINOS[self.current_piece_type]['shape']]
            self.current_x = BOARD_WIDTH // 2 - len(self.current_piece[0]) // 2
            self.current_y = 0
            self.holdPieceChanged.emit(self.hold_piece_type)
        
        self.can_hold = False
        self.update()
    
    def get_ghost_position(self):
        ghost_y = self.current_y
        while self.is_valid_position(self.current_piece, self.current_x, ghost_y + 1):
            ghost_y += 1
        return ghost_y
    
    def lock_piece(self):
        for row_idx, row in enumerate(self.current_piece):
            for col_idx, cell in enumerate(row):
                if cell:
                    y = self.current_y + row_idx
                    x = self.current_x + col_idx
                    if y >= 0:
                        self.board[y][x] = self.current_piece_type
        
        self.clear_lines()
        self.spawn_new_piece()
        self.update()
    
    def clear_lines(self):
        lines_to_clear = []
        for i in range(BOARD_HEIGHT):
            if all(self.board[i]):
                lines_to_clear.append(i)
        
        if lines_to_clear:
            for i in lines_to_clear:
                del self.board[i]
                self.board.insert(0, [None for _ in range(BOARD_WIDTH)])
            
            lines_count = len(lines_to_clear)
            self.lines_cleared += lines_count
            
            points = [0, SCORE_SINGLE_LINE, SCORE_DOUBLE_LINE, SCORE_TRIPLE_LINE, SCORE_TETRIS]
            self.score += points[lines_count] * self.level
            
            new_level = self.lines_cleared // LINES_PER_LEVEL + 1
            if new_level > self.level:
                self.level = new_level
                self.levelChanged.emit(self.level)
                new_speed = max(MIN_SPEED, INITIAL_SPEED - (self.level - 1) * SPEED_DECREASE_PER_LEVEL)
                self.timer.start(new_speed, self)
            
            self.scoreChanged.emit(self.score)
            self.linesChanged.emit(self.lines_cleared)
            self.check_joker_earn()
    
    def get_play_time(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            return f"{minutes:02d}:{seconds:02d}"
        return "00:00"
    
    def game_over_action(self):
        self.is_game_over = True
        self.timer.stop()
        self.gameOver.emit()
    
    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.is_valid_position(self.current_piece, self.current_x, self.current_y + 1):
                self.current_y += 1
            else:
                self.lock_piece()
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.contentsRect()
        
        # Kare hücre boyutu hesapla (en küçük değeri kullan)
        cell_size = min(rect.width() // BOARD_WIDTH, rect.height() // BOARD_HEIGHT)
        
        # Tahta boyutlarını hesapla
        board_width = BOARD_WIDTH * cell_size
        board_height = BOARD_HEIGHT * cell_size
        
        # Tahtayı ortala
        board_left = rect.left() + (rect.width() - board_width) // 2
        board_top = rect.top() + (rect.height() - board_height) // 2
        
        # Yerleşik blokları çiz (düz parlak renk)
        for i in range(BOARD_HEIGHT):
            for j in range(BOARD_WIDTH):
                x = board_left + j * cell_size
                y = board_top + i * cell_size
                
                if self.board[i][j] is not None:
                    # self.draw_square(painter, x, y, cell_size, TETROMINOS[self.board[i][j]]['color'], is_falling=False)
                    self.draw_square_v2(painter, x, y, cell_size, TETROMINOS[self.board[i][j]]['color'], is_falling=True)
                else:
                    painter.setPen(QPen(QColor(40, 40, 40)))
                    painter.drawRect(x, y, cell_size, cell_size)
        
        # Gölge parça
        if self.current_piece and not self.is_paused:
            ghost_y = self.get_ghost_position()
            for row_idx, row in enumerate(self.current_piece):
                for col_idx, cell in enumerate(row):
                    if cell:
                        # x = board_left + (self.current_x + col_idx) * cell_size
                        # y = board_top + (ghost_y + row_idx) * cell_size
                        # ghost_color = QColor(TETROMINOS[self.current_piece_type]['color'])
                        # ghost_color.setAlpha(50)
                        # painter.fillRect(x + 1, y + 1, cell_size - 2, cell_size - 2, ghost_color)
                        x = board_left + (self.current_x + col_idx) * cell_size
                        y = board_top + (ghost_y + row_idx) * cell_size
                        ghost_color = TETROMINOS[self.current_piece_type]['color']
                        ghost_color.setAlpha(50)
                        self.draw_square(painter, x, y, cell_size, ghost_color, ghost=True)

        
        # Düşen parça (3D efekt)
        if self.current_piece and not self.is_paused:
            for row_idx, row in enumerate(self.current_piece):
                for col_idx, cell in enumerate(row):
                    if cell:
                        # x = board_left + (self.current_x + col_idx) * cell_size
                        # y = board_top + (self.current_y + row_idx) * cell_size
                        # self.draw_square(painter, x, y, cell_size, TETROMINOS[self.current_piece_type]['color'], is_falling=True)
                        x = board_left + (self.current_x + col_idx) * cell_size
                        y = board_top + (self.current_y + row_idx) * cell_size
                        self.draw_square(painter, x, y, cell_size, TETROMINOS[self.current_piece_type]['color'])        


        if self.is_paused:
            # Yarı saydam arka plan
            overlay = QColor(0, 0, 0, 180)
            painter.fillRect(rect, overlay)
            
            # Yazı için kutu
            text = 'DURAKLATILDI'
            painter.setFont(QFont('Arial', FONT_SIZE_TITLE, QFont.Bold))
            text_rect = painter.fontMetrics().boundingRect(text)
            
            box_width = text_rect.width() + 100
            box_height = text_rect.height() + 50
            box_x = rect.center().x() - box_width // 2
            box_y = rect.center().y() - box_height // 2
            
            # Kutu arka planı
            painter.fillRect(box_x, box_y, box_width, box_height, QColor(30, 30, 30, 230))
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawRect(box_x, box_y, box_width, box_height)
            
            # Yazı
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect, Qt.AlignCenter, text)
    
    def draw_square_v2(self, painter, x, y, size, color, is_falling=False):
        """
        Kare çiz - düşen parça için neon glow efekt, yerleşikler için düz renk
        """
        if is_falling:
            # Neon glow efekt katmanları (dıştan içe)
            # Dış glow - en parlak ve geniş
            glow_color_outer = QColor(color)
            glow_color_outer.setAlpha(80)
            painter.setPen(QPen(glow_color_outer, 6))
            painter.drawRect(x - 2, y - 2, size + 4, size + 4)
            
            # Orta glow
            glow_color_mid = QColor(color)
            glow_color_mid.setAlpha(150)
            painter.setPen(QPen(glow_color_mid, 4))
            painter.drawRect(x - 1, y - 1, size + 2, size + 2)
            
            # İç glow - en parlak ince çizgi
            glow_color_inner = QColor(color.lighter(180))
            glow_color_inner.setAlpha(255)
            painter.setPen(QPen(glow_color_inner, 2))
            painter.drawRect(x, y, size, size)
        
        # Ana dolgu - parlak renk
        painter.fillRect(x + 1, y + 1, size - 2, size - 2, color)
        
        if is_falling:
            # Düşen parça için 3D efekt
            light_color = QColor(color)
            light_color.setAlpha(255)
            light_factor = 160  # Daha parlak
            light_color = light_color.lighter(light_factor)
            
            dark_color = QColor(color)
            dark_color.setAlpha(255)
            dark_factor = 110  # Daha az koyu
            dark_color = dark_color.darker(dark_factor)
            
            # Üst ve sol kenar (çok parlak)
            painter.setPen(QPen(light_color, 2))
            painter.drawLine(x + 1, y + 1, x + size - 2, y + 1)
            painter.drawLine(x + 1, y + 1, x + 1, y + size - 2)
            
            # Alt ve sağ kenar (hafif koyu)
            painter.setPen(QPen(dark_color, 2))
            painter.drawLine(x + 1, y + size - 1, x + size - 1, y + size - 1)
            painter.drawLine(x + size - 1, y + 1, x + size - 1, y + size - 1)
            
            # İç highlight - ekstra parlaklık
            highlight = QColor(255, 255, 255, 100)
            painter.fillRect(x + 2, y + 2, size - 6, size - 6, highlight)
        else:
            # Yerleşik parçalar için sadece ince kenarlık
            painter.setPen(QPen(QColor(60, 60, 60), 1))
            painter.drawRect(x, y, size, size)
    
    def draw_square(self, painter, x, y, size, color, ghost=False):
        # Ana dolgu - parlak renk
        painter.fillRect(x + 1, y + 1, size - 2, size - 2, color)
        
        if not ghost:
            # 3D efekt için daha yumuşak tonlar
            light_color = QColor(color)
            light_color.setAlpha(255)
            light_factor = 140  # Daha az parlaklık farkı
            light_color = light_color.lighter(light_factor)
            
            dark_color = QColor(color)
            dark_color.setAlpha(255)
            dark_factor = 120  # Daha az koyuluk farkı
            dark_color = dark_color.darker(dark_factor)
            
            # Üst ve sol kenar (açık)
            painter.setPen(QPen(light_color, 2))
            painter.drawLine(x + 1, y + 1, x + size - 2, y + 1)  # Üst
            painter.drawLine(x + 1, y + 1, x + 1, y + size - 2)  # Sol
            
            # Alt ve sağ kenar (koyu)
            painter.setPen(QPen(dark_color, 2))
            painter.drawLine(x + 1, y + size - 1, x + size - 1, y + size - 1)  # Alt
            painter.drawLine(x + size - 1, y + 1, x + size - 1, y + size - 1)  # Sağ

    def square_width(self):
        # Artık kullanılmıyor ama uyumluluk için bırakıldı
        cell_size = min(self.contentsRect().width() // BOARD_WIDTH, 
                       self.contentsRect().height() // BOARD_HEIGHT)
        return cell_size
    
    def square_height(self):
        # Artık kullanılmıyor ama uyumluluk için bırakıldı
        cell_size = min(self.contentsRect().width() // BOARD_WIDTH, 
                       self.contentsRect().height() // BOARD_HEIGHT)
        return cell_size
    
    def keyPressEvent(self, event):
        """TetrisBoard için klavye olayları - BU METOD TetrisBoard SINIFINDA"""
        key = event.key()
        
        if key == Qt.Key_P:
            self.pause()
        elif key == Qt.Key_F1:
            self.window().show_help()
        elif key == Qt.Key_F2:
            self.change_current_piece()
        elif key == Qt.Key_F3:
            self.use_joker()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            if not self.timer.isActive():
                self.start()
        elif key == Qt.Key_R:
            self.window().restart_game()
        elif key == Qt.Key_Left:
            self.move_piece(-1)
        elif key == Qt.Key_Right:
            self.move_piece(1)
        elif key == Qt.Key_Down:
            self.soft_drop()
        elif key == Qt.Key_Up or key == Qt.Key_Z:
            self.rotate_piece()
        elif key == Qt.Key_Space:
            self.hard_drop()
        elif key == Qt.Key_H or key == Qt.Key_C:
            self.hold_piece()

# ============================================================================
# ÖNİZLEME WİDGET'I
# ============================================================================

class PreviewWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.piece_type = None
        self.setMinimumSize(120, 120)
        self.setStyleSheet('background-color: #1a1a1a; border: 2px solid #333;')
    
    def set_piece(self, piece_type):
        self.piece_type = piece_type
        self.update()
    
    def paintEvent(self, event):
        if not self.piece_type:
            return
        
        painter = QPainter(self)
        piece = TETROMINOS[self.piece_type]['shape']
        color = TETROMINOS[self.piece_type]['color']
        
        cell_size = min(self.width() // 5, self.height() // 5)
        offset_x = (self.width() - len(piece[0]) * cell_size) // 2
        offset_y = (self.height() - len(piece) * cell_size) // 2
        
        for row_idx, row in enumerate(piece):
            for col_idx, cell in enumerate(row):
                if cell:
                    x = offset_x + col_idx * cell_size
                    y = offset_y + row_idx * cell_size
                    # Düz parlak renk
                    painter.fillRect(x + 1, y + 1, cell_size - 2, cell_size - 2, color)
                    
                    # İnce kenarlık
                    painter.setPen(QPen(QColor(60, 60, 60), 1))
                    painter.drawRect(x, y, cell_size, cell_size)

# ============================================================================
# ANA OYUN PENCERESİ
# ============================================================================

class TetrisOyunu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.high_score_manager = HighScoreManager()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('🎮 Tetris Pro')
        self.setStyleSheet('background-color: #0a0a0a; color: white;')
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        # Sol panel (Sakla + Butonlar + Kontroller)
        left_panel = QVBoxLayout()
        
        # Sakla kutusu
        hold_label = QLabel('SAKLA (H/C)')
        hold_label.setAlignment(Qt.AlignCenter)
        hold_label.setStyleSheet(f'font-size: {FONT_SIZE_MEDIUM}px; font-weight: bold; margin: 5px;')
        self.hold_preview = PreviewWidget()
        left_panel.addWidget(hold_label)
        left_panel.addWidget(self.hold_preview)
        
        # Butonlar
        self.start_btn = QPushButton('▶ Başlat (Enter)')
        self.pause_btn = QPushButton('⏸ Duraklat (P)')
        self.restart_btn = QPushButton('🔄 Yeniden Başlat (R)')
        self.help_btn = QPushButton('📖 Yardım (F1)')
        self.highscore_btn = QPushButton('🏆 En Yüksek Skorlar')
        
        for btn in [self.start_btn, self.pause_btn, self.restart_btn, self.help_btn, self.highscore_btn]:
            btn.setStyleSheet(f'''
                QPushButton {{
                    background-color: #2a2a2a;
                    border: 2px solid #444;
                    padding: 12px;
                    font-size: {FONT_SIZE_SMALL}px;
                    font-weight: bold;
                    margin: 3px;
                }}
                QPushButton:hover {{
                    background-color: #3a3a3a;
                }}
                QPushButton:pressed {{
                    background-color: #1a1a1a;
                }}
            ''')
            btn.setFocusPolicy(Qt.NoFocus)
        
        self.start_btn.clicked.connect(self.start_game)
        self.pause_btn.clicked.connect(self.pause_game)
        self.restart_btn.clicked.connect(self.restart_game)
        self.help_btn.clicked.connect(self.show_help)
        self.highscore_btn.clicked.connect(self.show_high_scores)
        
        left_panel.addWidget(self.start_btn)
        left_panel.addWidget(self.pause_btn)
        left_panel.addWidget(self.restart_btn)
        left_panel.addWidget(self.help_btn)
        left_panel.addWidget(self.highscore_btn)
        
        # Kontroller
        controls_frame = QFrame()
        controls_frame.setStyleSheet('background-color: #1a1a1a; border: 2px solid #333; padding: 15px;')
        controls_layout = QVBoxLayout()
        
        controls_title = QLabel('KONTROLLER')
        controls_title.setAlignment(Qt.AlignCenter)
        controls_title.setStyleSheet(f'font-weight: bold; margin-bottom: 8px; font-size: {FONT_SIZE_MEDIUM}px;')
        
        controls_text = QLabel(
            '← → : Hareket\n'
            '↑ Z : Döndür\n'
            '↓ : Hızlı Düşüş\n'
            'Space : Anında Düşür\n'
            'Enter : Başlat\n'
            'R : Yeniden Başlat\n'
            'P : Duraklat\n'
            'H/C : Sakla\n'
            'F1 : Yardım\n'
            'F2 : Parça Değiştir\n'
            'F3 : Joker Kullan'
        )
        controls_text.setStyleSheet(f'font-size: {FONT_SIZE_CONTROLS}px; line-height: 1.8;')
        
        controls_layout.addWidget(controls_title)
        controls_layout.addWidget(controls_text)
        controls_frame.setLayout(controls_layout)
        left_panel.addWidget(controls_frame)
        
        left_panel.addStretch()
        
        # Oyun tahtası
        self.board = TetrisBoard(self)
        self.board.setMinimumSize(300, 600)
        self.board.scoreChanged.connect(self.update_score)
        self.board.levelChanged.connect(self.update_level)
        self.board.linesChanged.connect(self.update_lines)
        self.board.jokersChanged.connect(self.update_jokers)
        self.board.nextPieceChanged.connect(self.update_next_piece)
        self.board.holdPieceChanged.connect(self.update_hold_piece)
        self.board.gameOver.connect(self.handle_game_over)
        
        # Sağ panel (Sıradaki + İstatistikler)
        right_panel = QVBoxLayout()
        
        # Sıradaki parça
        next_label = QLabel('SIRADAKİ')
        next_label.setAlignment(Qt.AlignCenter)
        next_label.setStyleSheet(f'font-size: {FONT_SIZE_MEDIUM}px; font-weight: bold; margin: 5px;')
        self.next_preview = PreviewWidget()
        
        right_panel.addWidget(next_label)
        right_panel.addWidget(self.next_preview)
        
        # İstatistikler
        stats_frame = QFrame()
        stats_frame.setStyleSheet('background-color: #1a1a1a; border: 2px solid #333; padding: 15px;')
        stats_layout = QVBoxLayout()
        
        self.score_label = QLabel('Skor: 0')
        self.level_label = QLabel('Seviye: 1')
        self.lines_label = QLabel('Satır: 0')
        self.joker_label = QLabel('🃏 Joker: 0')
        
        for label in [self.score_label, self.level_label, self.lines_label, self.joker_label]:
            label.setStyleSheet(f'font-size: {FONT_SIZE_LARGE}px; margin: 8px; font-weight: bold;')
            stats_layout.addWidget(label)
        
        stats_frame.setLayout(stats_layout)
        right_panel.addWidget(stats_frame)
        
        right_panel.addStretch()
        
        main_layout.addLayout(left_panel)
        main_layout.addWidget(self.board)
        main_layout.addLayout(right_panel)
        
        central_widget.setLayout(main_layout)
        
        self.resize(900, 700)
        
        # Başlangıçta focus'u oyun tahtasına ver
        self.board.setFocus()
    
    def showEvent(self, event):
        """Pencere gösterildiğinde merkeze al"""
        super().showEvent(event)
        self.center_window()
    
    def center_window(self):
        frame_geo = self.frameGeometry()
        screen_center = QApplication.desktop().screenGeometry().center()
        frame_geo.moveCenter(screen_center)
        self.move(frame_geo.topLeft())
    
    def update_score(self, score):
        self.score_label.setText(f'Skor: {score}')
    
    def update_level(self, level):
        self.level_label.setText(f'Seviye: {level}')
    
    def update_lines(self, lines):
        self.lines_label.setText(f'Satır: {lines}')
    
    def update_jokers(self, jokers):
        self.joker_label.setText(f'🃏 Joker: {jokers}')
    
    def update_next_piece(self, piece_type):
        self.next_preview.set_piece(piece_type)
    
    def update_hold_piece(self, piece_type):
        self.hold_preview.set_piece(piece_type)
    
    def start_game(self):
        self.board.start()
        self.board.setFocus()  # Focus'u oyun tahtasına geri ver
    
    def pause_game(self):
        self.board.pause()
        self.board.setFocus()  # Focus'u oyun tahtasına geri ver
    
    def restart_game(self):
        self.board.init_board()
        self.update_score(0)
        self.update_level(1)
        self.update_lines(0)
        self.update_jokers(0)
        self.board.start()
        self.board.setFocus()  # Focus'u oyun tahtasına geri ver
    
    def handle_game_over(self):
        score = self.board.score
        play_time = self.board.get_play_time()
        date_time = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        if self.high_score_manager.is_high_score(score):
            name, ok = QInputDialog.getText(self, 'Yüksek Skor!', 
                                           f'Tebrikler! Skorunuz: {score}\nİsminizi girin:')
            if ok and name:
                self.high_score_manager.add_score(name, score, self.board.level, 
                                                 self.board.lines_cleared, play_time, date_time)
                self.show_high_scores()
        else:
            QMessageBox.information(self, 'Oyun Bitti', 
                                   f'Oyun Bitti!\n\n'
                                   f'Skor: {score}\n'
                                   f'Seviye: {self.board.level}\n'
                                   f'Satır: {self.board.lines_cleared}\n'
                                   f'Süre: {play_time}')
    
    def show_high_scores(self):
        dialog = HighScoreDialog(self.high_score_manager.scores, self)
        dialog.exec_()
        self.board.setFocus()  # Dialog kapandıktan sonra focus'u geri ver
    
    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()
        self.board.setFocus()  # Dialog kapandıktan sonra focus'u geri ver

    def keyPressEvent(self, event):
        key = event.key()
        
        if key == Qt.Key_P:
            self.pause()
        elif key == Qt.Key_F1:
            self.window().show_help()
        elif key == Qt.Key_F2:
            self.change_current_piece()
        elif key == Qt.Key_F3:
            self.use_joker()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            # Enter ile oyunu başlat
            if not self.timer.isActive():
                self.start()
        elif key == Qt.Key_R:
            # R ile yeniden başlat
            self.window().restart_game()
        elif key == Qt.Key_Left:
            self.move_piece(-1)
        elif key == Qt.Key_Right:
            self.move_piece(1)
        elif key == Qt.Key_Down:
            self.soft_drop()
        elif key == Qt.Key_Up or key == Qt.Key_Z:
            self.rotate_piece()
        elif key == Qt.Key_Space:
            self.hard_drop()
        elif key == Qt.Key_H or key == Qt.Key_C:
            self.hold_piece()
