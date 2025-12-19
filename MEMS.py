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
    def __init__(self, x, y, controller=None):
        super().__init__()
        self.x = x
        self.y = y
        self.state = 0  # 0, 1, or 2
        self.controller = controller
        self.setFixedSize(QSize(15, 15))
        self.setCheckable(False)
        self.setMouseTracking(True)  # Enable mouse tracking for hover events
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

    def mousePressEvent(self, event):
        """Handle mouse press - start drawing and paint this pixel"""
        if event.button() == Qt.MouseButton.LeftButton and self.controller:
            self.controller.is_drawing = True
            self.set_state(self.controller.selected_pen)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move - paint if drawing mode is active"""
        if self.controller and self.controller.is_drawing:
            self.set_state(self.controller.selected_pen)
        super().mouseMoveEvent(event)


class MEMSController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.x_pixels = 64
        self.y_pixels = 48
        self.total_pixels = self.x_pixels * self.y_pixels
        self.pixel_buttons = []
        self.selected_pen = 1  # Default pen state is 1 (On)
        self.is_drawing = False  # Track if mouse button is held down

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

        # Pen tool selector
        pen_label = QLabel('Pen:')
        control_layout.addWidget(pen_label)

        self.pen_selector = QComboBox()
        self.pen_selector.addItems(['0 - Inactive (grey)', '1 - On (green)', '2 - Off (red)'])
        self.pen_selector.setCurrentIndex(1)  # Default to state 1 (On)
        self.pen_selector.currentIndexChanged.connect(self.pen_changed)
        control_layout.addWidget(self.pen_selector)

        control_layout.addSpacing(20)  # Add some space

        self.load_image_btn = QPushButton('Load Image')
        self.load_image_btn.clicked.connect(self.load_image)
        control_layout.addWidget(self.load_image_btn)
        
        self.clear_btn = QPushButton('Clear All')
        self.clear_btn.clicked.connect(self.clear_all)
        control_layout.addWidget(self.clear_btn)
        
        self.fill_state_label = QLabel('Fill State:')
        control_layout.addWidget(self.fill_state_label)
        
        self.fill_state_combo = QComboBox()
        self.fill_state_combo.addItems(['0 - Inactive (grey)', '1 - On (green)', '2 - Off (red)'])
        control_layout.addWidget(self.fill_state_combo)
        
        self.fill_all_btn = QPushButton('Fill All')
        self.fill_all_btn.clicked.connect(self.fill_all)
        control_layout.addWidget(self.fill_all_btn)
        
        left_layout.addLayout(control_layout)
        
        # Pixel grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.grid_widget = QWidget()
        self.grid_widget.setMouseTracking(True)  # Enable mouse tracking on grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_widget.setLayout(self.grid_layout)

        # Create pixel buttons
        # Zemax numbering: bottom-left is pixel 1, increment in +X, then +Y
        # So we create from bottom to top
        for y in range(self.y_pixels):
            for x in range(self.x_pixels):
                pixel_btn = PixelButton(x, y, controller=self)
                pixel_btn.clicked.connect(lambda checked, btn=pixel_btn: self.pixel_clicked(btn))
                # Display from top to bottom (reverse Y for display)
                self.grid_layout.addWidget(pixel_btn, self.y_pixels - 1 - y, x)
                self.pixel_buttons.append(pixel_btn)
        
        # Install event filter on grid widget to handle drag painting
        self.grid_widget.installEventFilter(self)

        scroll_area.setWidget(self.grid_widget)
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
        angle0_layout.addWidget(QLabel("Angle 0 (Inactive):"))
        self.angle0_spin = QSpinBox()
        self.angle0_spin.setRange(-90, 90)
        self.angle0_spin.setValue(0)
        self.angle0_spin.setSuffix("°")
        angle0_layout.addWidget(self.angle0_spin)
        angle_layout.addLayout(angle0_layout)

        angle1_layout = QHBoxLayout()
        angle1_layout.addWidget(QLabel("Angle 1 (On):"))
        self.angle1_spin = QSpinBox()
        self.angle1_spin.setRange(-90, 90)
        self.angle1_spin.setValue(12)
        self.angle1_spin.setSuffix("°")
        angle1_layout.addWidget(self.angle1_spin)
        angle_layout.addLayout(angle1_layout)

        angle2_layout = QHBoxLayout()
        angle2_layout.addWidget(QLabel("Angle 2 (Off):"))
        self.angle2_spin = QSpinBox()
        self.angle2_spin.setRange(-90, 90)
        self.angle2_spin.setValue(-12)
        self.angle2_spin.setSuffix("°")
        angle2_layout.addWidget(self.angle2_spin)
        angle_layout.addLayout(angle2_layout)
        
        angle_group.setLayout(angle_layout)
        right_layout.addWidget(angle_group)

        # Table orientation selector
        table_orient_layout = QHBoxLayout()
        table_orient_label = QLabel('Table Format:')
        table_orient_layout.addWidget(table_orient_label)

        self.table_orient_combo = QComboBox()
        self.table_orient_combo.addItems(['Parameters as Rows', 'Parameters as Columns'])
        self.table_orient_combo.currentIndexChanged.connect(lambda: self.calculate_parameters())
        table_orient_layout.addWidget(self.table_orient_combo)
        right_layout.addLayout(table_orient_layout)

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
    
    def mouseReleaseEvent(self, event):
        """Stop drawing when mouse button is released"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_drawing = False
        super().mouseReleaseEvent(event)

    def eventFilter(self, obj, event):
        """Filter events on grid widget to enable drag painting"""
        if obj == self.grid_widget and self.is_drawing:
            if event.type() == event.Type.MouseMove:
                # Find which button is under the mouse
                widget = self.grid_widget.childAt(event.pos())
                if isinstance(widget, PixelButton):
                    widget.set_state(self.selected_pen)
        return super().eventFilter(obj, event)

    def pen_changed(self, index):
        """Update selected pen state when user changes pen selector"""
        self.selected_pen = index

    def pixel_clicked(self, pixel_btn):
        """Set pixel to selected pen state when clicked"""
        pixel_btn.set_state(self.selected_pen)
        
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

                        # Get pixel value from image (flip Y to correct orientation)
                        img_value = img_bw[self.y_pixels - 1 - y, x]

                        # Set state: black (0) -> On (1), white (1) -> Off (2)
                        state = 2 if img_value == 1 else 1
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
            param_num = 10 + (start - 1) // 15
            parameters.append((param_num, start_pixel, end_pixel, value))

        # Format output based on table orientation
        output = f"MEMS Configuration: {self.x_pixels} x {self.y_pixels} pixels\n"
        output += f"Total pixels: {self.total_pixels}\n"
        output += f"P-Flag: 2 (Individual pixel addressing)\n\n"
        output += f"Angle 0 (Inactive): {self.angle0_spin.value()}°\n"
        output += f"Angle 1 (On): {self.angle1_spin.value()}°\n"
        output += f"Angle 2 (Off): {self.angle2_spin.value()}°\n\n"

        table_format = self.table_orient_combo.currentIndex()

        if table_format == 0:  # Parameters as Rows
            output += "Parameter\tPixels\tValue\n"
            for param_num, start, end, value in parameters:
                output += f"{param_num}\t{start}-{end}\t{value}\n"
        else:  # Parameters as Columns
            # Create header row with parameter numbers
            param_headers = "\t".join([str(p[0]) for p in parameters])
            output += f"Parameter\t{param_headers}\n"

            # Create pixel ranges row
            pixel_ranges = "\t".join([f"{p[1]}-{p[2]}" for p in parameters])
            output += f"Pixels\t{pixel_ranges}\n"

            # Create values row
            values = "\t".join([str(p[3]) for p in parameters])
            output += f"Value\t{values}\n"

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