#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the Export functionality in DosyaAnaliziPenceresi
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add the timer directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from timer_file_analyzer import DosyaAnaliziPenceresi

def test_export_functionality():
    """Test the export functionality by opening the file analyzer window"""
    app = QApplication(sys.argv)
    
    # Create the file analyzer window
    window = DosyaAnaliziPenceresi()
    window.show()
    
    print("File Analyzer window opened with Export button.")
    print("To test:")
    print("1. Click 'Klasör Seç' to select a folder")
    print("2. Wait for analysis to complete")
    print("3. Click 'Dışarıya Aktar' to export the table data")
    print("4. Select a location to save the txt file")
    print("5. Check the exported file for proper formatting")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_export_functionality()
