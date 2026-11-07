# ti_tetris_board.py
from PyQt5.QtWidgets import QFrame, QMessageBox
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
import random
import time
from datetime import datetime

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


class TetrisBoard(QFrame):
    """Tetris oyun tahtası bileşeni"""
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
                        x = board_left + (self.current_x + col_idx) * cell_size
                        y = board_top + (ghost_y + row_idx) * cell_size
                        ghost_color = TETROMINOS[self.current_piece_type]['color']
                        ghost_color.setAlpha(50)
                        self.draw_square(painter, x, y, cell_size, ghost_color, ghost=True)

        # Düşen parça
        if self.current_piece and not self.is_paused:
            for row_idx, row in enumerate(self.current_piece):
                for col_idx, cell in enumerate(row):
                    if cell:
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
            glow_color_outer = QColor(color)
            glow_color_outer.setAlpha(80)
            painter.setPen(QPen(glow_color_outer, 6))
            painter.drawRect(x - 2, y - 2, size + 4, size + 4)
            
            glow_color_mid = QColor(color)
            glow_color_mid.setAlpha(150)
            painter.setPen(QPen(glow_color_mid, 4))
            painter.drawRect(x - 1, y - 1, size + 2, size + 2)
            
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
            light_factor = 160
            light_color = light_color.lighter(light_factor)
            
            dark_color = QColor(color)
            dark_color.setAlpha(255)
            dark_factor = 110
            dark_color = dark_color.darker(dark_factor)
            
            # Üst ve sol kenar
            painter.setPen(QPen(light_color, 2))
            painter.drawLine(x + 1, y + 1, x + size - 2, y + 1)
            painter.drawLine(x + 1, y + 1, x + 1, y + size - 2)
            
            # Alt ve sağ kenar
            painter.setPen(QPen(dark_color, 2))
            painter.drawLine(x + 1, y + size - 1, x + size - 1, y + size - 1)
            painter.drawLine(x + size - 1, y + 1, x + size - 1, y + size - 1)
            
            # İç highlight
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
            light_color = QColor(color)
            light_color.setAlpha(255)
            light_factor = 140
            light_color = light_color.lighter(light_factor)
            
            dark_color = QColor(color)
            dark_color.setAlpha(255)
            dark_factor = 120
            dark_color = dark_color.darker(dark_factor)
            
            painter.setPen(QPen(light_color, 2))
            painter.drawLine(x + 1, y + 1, x + size - 2, y + 1)  # Üst
            painter.drawLine(x + 1, y + 1, x + 1, y + size - 2)  # Sol
            
            painter.setPen(QPen(dark_color, 2))
            painter.drawLine(x + 1, y + size - 1, x + size - 1, y + size - 1)  # Alt
            painter.drawLine(x + size - 1, y + 1, x + size - 1, y + size - 1)  # Sağ

    def square_width(self):
        cell_size = min(self.contentsRect().width() // BOARD_WIDTH, 
                       self.contentsRect().height() // BOARD_HEIGHT)
        return cell_size
    
    def square_height(self):
        cell_size = min(self.contentsRect().width() // BOARD_WIDTH, 
                       self.contentsRect().height() // BOARD_HEIGHT)
        return cell_size
    
    def keyPressEvent(self, event):
        """TetrisBoard için klavye olayları"""
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


class PreviewWidget(QFrame):
    """Sıradaki ve bekletilen parçayı çizen önizleme penceresi"""
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
                    painter.fillRect(x + 1, y + 1, cell_size - 2, cell_size - 2, color)
                    painter.setPen(QPen(QColor(60, 60, 60), 1))
                    painter.drawRect(x, y, cell_size, cell_size)

