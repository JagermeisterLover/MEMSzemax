import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QScrollArea,
                             QGridLayout, QFileDialog, QTextEdit, QComboBox,
                             QSpinBox, QGroupBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image
import numpy as np


class PixelButton(QPushButton):
    """Individual pixel button that can be in state 0, 1, or 2"""
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.state = 0  # 0, 1, or 2
        self.setFixedSize(QSize(15, 15))
        self.setCheckable(False)
        self.update_appearance()
        
    def update_appearance(self):
        if self.state == 0:
            self.setStyleSheet("background-color: gray; border: 1px solid black;")
        elif self.state == 1:
            self.setStyleSheet("background-color: green; border: 1px solid black;")
        elif self.state == 2:
            self.setStyleSheet("background-color: red; border: 1px solid black;")
    
    def set_state(self, state):
        self.state = state
        self.update_appearance()
    
    def cycle_state(self):
        self.state = (self.state + 1) % 3
        self.update_appearance()


class MEMSController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.x_pixels = 64
        self.y_pixels = 48
        self.total_pixels = self.x_pixels * self.y_pixels
        self.pixel_buttons = []
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('MEMS Pixel Controller (64x48)')
        self.setGeometry(100, 100, 1200, 900)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Left panel - pixel grid
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.load_image_btn = QPushButton('Load Image')
        self.load_image_btn.clicked.connect(self.load_image)
        control_layout.addWidget(self.load_image_btn)
        
        self.clear_btn = QPushButton('Clear All')
        self.clear_btn.clicked.connect(self.clear_all)
        control_layout.addWidget(self.clear_btn)
        
        self.fill_state_label = QLabel('Fill State:')
        control_layout.addWidget(self.fill_state_label)
        
        self.fill_state_combo = QComboBox()
        self.fill_state_combo.addItems(['0 (Off)', '1 (+angle)', '2 (-angle)'])
        control_layout.addWidget(self.fill_state_combo)
        
        self.fill_all_btn = QPushButton('Fill All')
        self.fill_all_btn.clicked.connect(self.fill_all)
        control_layout.addWidget(self.fill_all_btn)
        
        left_layout.addLayout(control_layout)
        
        # Pixel grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        grid_widget.setLayout(self.grid_layout)
        
        # Create pixel buttons
        # Zemax numbering: bottom-left is pixel 1, increment in +X, then +Y
        # So we create from bottom to top
        for y in range(self.y_pixels):
            for x in range(self.x_pixels):
                pixel_btn = PixelButton(x, y)
                pixel_btn.clicked.connect(lambda checked, btn=pixel_btn: self.pixel_clicked(btn))
                # Display from top to bottom (reverse Y for display)
                self.grid_layout.addWidget(pixel_btn, self.y_pixels - 1 - y, x)
                self.pixel_buttons.append(pixel_btn)
        
        scroll_area.setWidget(grid_widget)
        left_layout.addWidget(scroll_area)
        
        main_layout.addWidget(left_panel, stretch=2)
        
        # Right panel - output
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Angle configuration
        angle_group = QGroupBox("Angle Configuration")
        angle_layout = QVBoxLayout()
        
        angle0_layout = QHBoxLayout()
        angle0_layout.addWidget(QLabel("Angle 0 (State 0):"))
        self.angle0_spin = QSpinBox()
        self.angle0_spin.setRange(-90, 90)
        self.angle0_spin.setValue(0)
        self.angle0_spin.setSuffix("°")
        angle0_layout.addWidget(self.angle0_spin)
        angle_layout.addLayout(angle0_layout)
        
        angle1_layout = QHBoxLayout()
        angle1_layout.addWidget(QLabel("Angle 1 (State 1):"))
        self.angle1_spin = QSpinBox()
        self.angle1_spin.setRange(-90, 90)
        self.angle1_spin.setValue(5)
        self.angle1_spin.setSuffix("°")
        angle1_layout.addWidget(self.angle1_spin)
        angle_layout.addLayout(angle1_layout)
        
        angle2_layout = QHBoxLayout()
        angle2_layout.addWidget(QLabel("Angle 2 (State 2):"))
        self.angle2_spin = QSpinBox()
        self.angle2_spin.setRange(-90, 90)
        self.angle2_spin.setValue(-5)
        self.angle2_spin.setSuffix("°")
        angle2_layout.addWidget(self.angle2_spin)
        angle_layout.addLayout(angle2_layout)
        
        angle_group.setLayout(angle_layout)
        right_layout.addWidget(angle_group)
        
        # Calculate button
        self.calculate_btn = QPushButton('Calculate Parameters')
        self.calculate_btn.clicked.connect(self.calculate_parameters)
        self.calculate_btn.setStyleSheet("background-color: lightblue; font-weight: bold;")
        right_layout.addWidget(self.calculate_btn)
        
        # Output text
        output_label = QLabel('Zemax Parameters (P-Flag = 2):')
        right_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(self.font())
        right_layout.addWidget(self.output_text)
        
        # Copy button
        self.copy_btn = QPushButton('Copy to Clipboard')
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        right_layout.addWidget(self.copy_btn)
        
        main_layout.addWidget(right_panel, stretch=1)
        
        # Initial calculation
        self.calculate_parameters()
    
    def pixel_clicked(self, pixel_btn):
        """Cycle through states when pixel is clicked"""
        pixel_btn.cycle_state()
        
    def clear_all(self):
        """Set all pixels to state 0"""
        for btn in self.pixel_buttons:
            btn.set_state(0)
    
    def fill_all(self):
        """Fill all pixels with selected state"""
        state = self.fill_state_combo.currentIndex()
        for btn in self.pixel_buttons:
            btn.set_state(state)
    
    def load_image(self):
        """Load an image and convert to 64x48 black and white"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_name:
            try:
                # Load image
                img = Image.open(file_name)
                
                # Resize to 64x48
                img_resized = img.resize((self.x_pixels, self.y_pixels), Image.Resampling.LANCZOS)
                
                # Convert to grayscale
                img_gray = img_resized.convert('L')
                
                # Convert to numpy array
                img_array = np.array(img_gray)
                
                # Threshold to black and white (threshold at 128)
                img_bw = (img_array > 128).astype(int)
                
                # Update pixel buttons
                # Image coordinates: (0,0) is top-left
                # MEMS coordinates: pixel 1 is bottom-left, increment +X then +Y
                for y in range(self.y_pixels):
                    for x in range(self.x_pixels):
                        # Calculate pixel index in MEMS numbering
                        pixel_index = y * self.x_pixels + x
                        
                        # Get pixel value from image (flip Y for display)
                        img_value = img_bw[y, x]
                        
                        # Set state: 0 for black (off), 1 for white (on)
                        state = 1 if img_value == 1 else 0
                        self.pixel_buttons[pixel_index].set_state(state)
                
                self.statusBar().showMessage(f'Image loaded: {file_name}', 3000)
                
            except Exception as e:
                self.statusBar().showMessage(f'Error loading image: {str(e)}', 5000)
    
    def calculate_parameters(self):
        """Calculate Zemax parameter values"""
        # Get states for all pixels
        states = [btn.state for btn in self.pixel_buttons]
        
        # Calculate parameters for groups of 15 pixels
        parameters = []
        
        for i in range(0, self.total_pixels, 15):
            # Get up to 15 pixels
            group_states = states[i:i+15]
            
            # Calculate base-3 to base-10 conversion
            value = 0
            for j, state in enumerate(group_states):
                value += state * (3 ** j)
            
            # Store parameter with pixel range
            start_pixel = i + 1
            end_pixel = min(i + 15, self.total_pixels)
            parameters.append((start_pixel, end_pixel, value))
        
        # Format output
        output = f"MEMS Configuration: {self.x_pixels} x {self.y_pixels} pixels\n"
        output += f"Total pixels: {self.total_pixels}\n"
        output += f"P-Flag: 2 (Individual pixel addressing)\n\n"
        output += f"Angle 0: {self.angle0_spin.value()}°\n"
        output += f"Angle 1: {self.angle1_spin.value()}°\n"
        output += f"Angle 2: {self.angle2_spin.value()}°\n\n"
        output += "Parameters:\n"
        output += "-" * 60 + "\n"
        
        for start, end, value in parameters:
            param_num = 10 + (start - 1) // 15
            output += f"Parameter {param_num:3d} (Pixels {start:4d}-{end:4d}): {value}\n"
        
        self.output_text.setText(output)
        
        # Update status bar
        active_pixels = sum(1 for state in states if state != 0)
        self.statusBar().showMessage(
            f'Active pixels: {active_pixels}/{self.total_pixels}', 3000
        )
    
    def copy_to_clipboard(self):
        """Copy output text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_text.toPlainText())
        self.statusBar().showMessage('Copied to clipboard', 2000)


def main():
    app = QApplication(sys.argv)
    window = MEMSController()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()