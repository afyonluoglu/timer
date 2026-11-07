"""
TETRIS PRO - Gelişmiş Tetris Oyunu
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFrame, QInputDialog, QMessageBox,
                             QApplication)
from PyQt5.QtCore import Qt
from datetime import datetime

# Alt modüllerden içe aktarımlar
from ti_tetris_dialogs import (HighScoreManager, HighScoreDialog, HelpDialog,
                               HIGH_SCORE_FILE, FONT_SIZE_TITLE)
from ti_tetris_board import (TetrisBoard, PreviewWidget,
                             BOARD_WIDTH, BOARD_HEIGHT, INITIAL_SPEED, MIN_SPEED,
                             SPEED_DECREASE_PER_LEVEL, SCORE_SINGLE_LINE, SCORE_DOUBLE_LINE,
                             SCORE_TRIPLE_LINE, SCORE_TETRIS, SOFT_DROP_POINTS,
                             HARD_DROP_POINTS, LINES_PER_LEVEL, POINTS_PER_JOKER,
                             MAX_JOKERS, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM,
                             FONT_SIZE_SMALL, FONT_SIZE_CONTROLS, TETROMINOS)


# ============================================================================
# ANA OYUN PENCERESİ
# ============================================================================

class TetrisOyunu(QMainWindow):
    """Tetris Pro ana oyun penceresi"""
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
            self.pause_game()
        elif key == Qt.Key_F1:
            self.show_help()
        elif key == Qt.Key_F2:
            self.board.change_current_piece()
        elif key == Qt.Key_F3:
            self.board.use_joker()
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            if not self.board.timer.isActive():
                self.start_game()
        elif key == Qt.Key_R:
            self.restart_game()
        elif key == Qt.Key_Left:
            self.board.move_piece(-1)
        elif key == Qt.Key_Right:
            self.board.move_piece(1)
        elif key == Qt.Key_Down:
            self.board.soft_drop()
        elif key == Qt.Key_Up or key == Qt.Key_Z:
            self.board.rotate_piece()
        elif key == Qt.Key_Space:
            self.board.hard_drop()
        elif key == Qt.Key_H or key == Qt.Key_C:
            self.board.hold_piece()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    game = TetrisOyunu()
    game.show()
    sys.exit(app.exec_())
