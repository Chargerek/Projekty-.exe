"""
Aplikacja do przetwarzania obrazów - projekt grafika komputerowa.
Obsługuje wczytywanie PPM (P3, P6) i JPEG, filtry obrazowe, skalowanie i powiększanie.
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QSlider, QSpinBox,
    QGroupBox, QScrollArea, QTextEdit, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QImage, QPixmap, QPainter, QFont, QColor

from ppm_loader import load_ppm, PPMError
from image_filters import (
    apply_averaging_filter, apply_median_filter, apply_sobel_filter,
    apply_dilation, apply_erosion, rgb_to_binary
)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageViewer(QWidget):
    """Widget do wyświetlania obrazu z możliwością powiększania i przesuwania."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_image = None  # QImage
        self.display_image = None  # QPixmap
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.show_rgb_values = False
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        
    def set_image(self, image_data, width, height):
        """Ustawia obraz do wyświetlenia."""
        if image_data is None or len(image_data) == 0:
            return
        
        # Konwertuj listę krotek (R, G, B) na QImage
        image = QImage(width, height, QImage.Format.Format_RGB32)
        
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                if idx < len(image_data):
                    r, g, b = image_data[idx]
                    image.setPixel(x, y, QColor(r, g, b).rgb())
        
        self.original_image = image
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.update_display()
        
    def update_display(self):
        """Aktualizuje wyświetlany obraz z uwzględnieniem zoomu."""
        if self.original_image is None:
                    return
        
        # Skaluj obraz
        scaled_width = int(self.original_image.width() * self.zoom_factor)
        scaled_height = int(self.original_image.height() * self.zoom_factor)
        
        scaled_image = self.original_image.scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.display_image = QPixmap.fromImage(scaled_image)
        self.update()
        
    def set_zoom(self, factor):
        """Ustawia współczynnik powiększenia."""
        self.zoom_factor = max(0.1, min(10.0, factor))
        self.update_display()
        
    def zoom_in(self):
        """Powiększa obraz."""
        self.set_zoom(self.zoom_factor * 1.2)
        
    def zoom_out(self):
        """Pomniejsza obraz."""
        self.set_zoom(self.zoom_factor / 1.2)
        
    def reset_view(self):
        """Resetuje widok (zoom i przesunięcie)."""
        self.zoom_factor = 1.0
        self.pan_offset = QPoint(0, 0)
        self.update_display()
        
    def set_show_rgb(self, show):
        """Włącza/wyłącza wyświetlanie wartości RGB."""
        self.show_rgb_values = show
        self.update()
        
    def paintEvent(self, event):
        """Rysuje obraz."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.lightGray)
        
        if self.display_image is None:
            return
        
        # Oblicz pozycję obrazu z uwzględnieniem przesunięcia
        img_rect = self.display_image.rect()
        img_rect.moveTopLeft(self.pan_offset)
        
        # Rysuj obraz
        painter.drawPixmap(img_rect, self.display_image)
        
        # Wyświetl wartości RGB na pikselach przy dużym powiększeniu
        if self.show_rgb_values and self.zoom_factor >= 5.0:
            if self.original_image is None:
                return
                
            # Oblicz które piksele są widoczne
            visible_rect = self.rect().intersected(img_rect)
            
            # Skaluj współrzędne myszy do współrzędnych oryginalnego obrazu
            step = max(1, int(1.0 / self.zoom_factor * 10))
            
            for y in range(0, self.original_image.height(), step):
                for x in range(0, self.original_image.width(), step):
                    # Przekształć współrzędne obrazu na współrzędne ekranu
                    screen_x = int(x * self.zoom_factor) + self.pan_offset.x()
                    screen_y = int(y * self.zoom_factor) + self.pan_offset.y()
                    
                    if visible_rect.contains(screen_x, screen_y):
                        # Pobierz kolor piksela
                        color = self.original_image.pixelColor(x, y)
                        r, g, b = color.red(), color.green(), color.blue()
                        
                        # Rysuj tekst z wartościami RGB
                        painter.setPen(Qt.GlobalColor.white)
                        painter.setFont(QFont("Arial", 8))
                        text = f"R:{r}\nG:{g}\nB:{b}"
                        text_rect = painter.fontMetrics().boundingRect(text)
                        text_rect.moveTopLeft(QPoint(screen_x, screen_y))
                        
                        # Tło dla tekstu
                        painter.fillRect(text_rect.adjusted(-2, -2, 2, 2), QColor(0, 0, 0, 180))
                        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft, text)

    def mousePressEvent(self, event):
        """Rozpoczyna przesuwanie obrazu."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_pan_point = event.pos()

    def mouseMoveEvent(self, event):
        """Przesuwa obraz podczas przeciągania."""
        if event.buttons() & Qt.MouseButton.LeftButton and hasattr(self, 'last_pan_point'):
            delta = event.pos() - self.last_pan_point
            self.pan_offset += delta
            self.last_pan_point = event.pos()
            self.update()
            
    def wheelEvent(self, event):
        """Obsługuje scroll do zoomowania."""
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()


class MainWindow(QMainWindow):
    """Główne okno aplikacji."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aplikacja do Przetwarzania Obrazów")
        self.resize(1200, 800)
        
        # Dane obrazu
        self.image_data = None  # lista krotek (R, G, B)
        self.image_width = 0
        self.image_height = 0
        self.original_image_data = None  # kopia oryginalna
        
        # Element strukturyzujący dla dylatacji/erozji
        self.structuring_element = [
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ]
        
        self.init_ui()
        
    def init_ui(self):
        """Inicjalizuje interfejs użytkownika."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # Lewy panel - kontrolki
        control_panel = QWidget()
        control_panel.setFixedWidth(300)
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)
        
        # === Wczytywanie i zapisywanie ===
        load_group = QGroupBox("Wczytywanie i zapisywanie")
        load_layout = QVBoxLayout()
        load_group.setLayout(load_layout)
        
        self.btn_load_ppm = QPushButton("Wczytaj PPM")
        self.btn_load_jpeg = QPushButton("Wczytaj JPEG")
        self.btn_save_jpeg = QPushButton("Zapisz JPEG")
        
        self.btn_load_ppm.clicked.connect(self.load_ppm_file)
        self.btn_load_jpeg.clicked.connect(self.load_jpeg_file)
        self.btn_save_jpeg.clicked.connect(self.save_jpeg_file)
        
        load_layout.addWidget(self.btn_load_ppm)
        load_layout.addWidget(self.btn_load_jpeg)
        load_layout.addWidget(self.btn_save_jpeg)
        
        # Suwak jakości JPEG
        jpeg_quality_layout = QHBoxLayout()
        jpeg_quality_layout.addWidget(QLabel("Jakość JPEG:"))
        self.jpeg_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.jpeg_quality_slider.setMinimum(1)
        self.jpeg_quality_slider.setMaximum(100)
        self.jpeg_quality_slider.setValue(95)
        self.jpeg_quality_label = QLabel("95")
        self.jpeg_quality_slider.valueChanged.connect(
            lambda v: self.jpeg_quality_label.setText(str(v))
        )
        jpeg_quality_layout.addWidget(self.jpeg_quality_slider)
        jpeg_quality_layout.addWidget(self.jpeg_quality_label)
        load_layout.addLayout(jpeg_quality_layout)
        
        control_layout.addWidget(load_group)
        
        # === Filtry ===
        filters_group = QGroupBox("Filtry obrazowe")
        filters_layout = QVBoxLayout()
        filters_group.setLayout(filters_layout)
        
        self.btn_averaging = QPushButton("Filtr wygładzający")
        self.btn_median = QPushButton("Filtr medianowy")
        self.btn_sobel = QPushButton("Filtr Sobel (krawędzie)")
        self.btn_reset = QPushButton("Przywróć oryginał")
        
        self.btn_averaging.clicked.connect(self.apply_averaging)
        self.btn_median.clicked.connect(self.apply_median)
        self.btn_sobel.clicked.connect(self.apply_sobel)
        self.btn_reset.clicked.connect(self.reset_image)
        
        filters_layout.addWidget(self.btn_averaging)
        filters_layout.addWidget(self.btn_median)
        filters_layout.addWidget(self.btn_sobel)
        filters_layout.addWidget(self.btn_reset)
        
        # Rozmiar jądra dla filtrów
        kernel_layout = QHBoxLayout()
        kernel_layout.addWidget(QLabel("Rozmiar jądra:"))
        self.kernel_size_spin = QSpinBox()
        self.kernel_size_spin.setMinimum(3)
        self.kernel_size_spin.setMaximum(15)
        self.kernel_size_spin.setValue(3)
        self.kernel_size_spin.setSingleStep(2)
        kernel_layout.addWidget(self.kernel_size_spin)
        filters_layout.addLayout(kernel_layout)
        
        control_layout.addWidget(filters_group)
        
        # === Dylatacja i erozja ===
        morph_group = QGroupBox("Operacje morfologiczne")
        morph_layout = QVBoxLayout()
        morph_group.setLayout(morph_layout)
        
        self.btn_binary = QPushButton("Konwertuj na binarny")
        self.btn_dilation = QPushButton("Dylatacja")
        self.btn_erosion = QPushButton("Erozja")
        
        self.btn_binary.clicked.connect(self.convert_to_binary)
        self.btn_dilation.clicked.connect(self.apply_dilation_filter)
        self.btn_erosion.clicked.connect(self.apply_erosion_filter)
        
        morph_layout.addWidget(self.btn_binary)
        morph_layout.addWidget(self.btn_dilation)
        morph_layout.addWidget(self.btn_erosion)
        
        # Edycja elementu strukturyzującego
        se_label = QLabel("Element strukturyzujący:")
        morph_layout.addWidget(se_label)
        
        self.se_text = QTextEdit()
        self.se_text.setMaximumHeight(100)
        self.se_text.setPlainText("1 1 1\n1 1 1\n1 1 1")
        self.se_text.textChanged.connect(self.update_structuring_element)
        morph_layout.addWidget(self.se_text)
        
        control_layout.addWidget(morph_group)
        
        # === Skalowanie kolorów ===
        scale_group = QGroupBox("Skalowanie liniowe kolorów")
        scale_layout = QVBoxLayout()
        scale_group.setLayout(scale_layout)
        
        self.btn_scale_colors = QPushButton("Zastosuj skalowanie")
        self.btn_scale_colors.clicked.connect(self.scale_colors)
        scale_layout.addWidget(self.btn_scale_colors)
        
        control_layout.addWidget(scale_group)
        
        # === Kontrola widoku ===
        # Najpierw tworzymy viewer, żeby móc połączyć przyciski
        self.viewer = ImageViewer()
        
        view_group = QGroupBox("Kontrola widoku")
        view_layout = QVBoxLayout()
        view_group.setLayout(view_layout)
        
        self.btn_zoom_in = QPushButton("Powiększ (+)")
        self.btn_zoom_out = QPushButton("Pomniejsz (-)")
        self.btn_reset_view = QPushButton("Reset widoku")
        self.btn_show_rgb = QPushButton("Pokaż RGB (włącz)")
        self.show_rgb_enabled = False
        
        self.btn_zoom_in.clicked.connect(self.viewer.zoom_in)
        self.btn_zoom_out.clicked.connect(self.viewer.zoom_out)
        self.btn_reset_view.clicked.connect(self.viewer.reset_view)
        self.btn_show_rgb.clicked.connect(self.toggle_show_rgb)
        
        view_layout.addWidget(self.btn_zoom_in)
        view_layout.addWidget(self.btn_zoom_out)
        view_layout.addWidget(self.btn_reset_view)
        view_layout.addWidget(self.btn_show_rgb)
        
        control_layout.addWidget(view_group)
        
        control_layout.addStretch()
        
        # === Główny obszar wyświetlania === (dodajemy na końcu do main_layout)
        main_layout.addWidget(self.viewer, stretch=1)
        
    def toggle_show_rgb(self):
        """Przełącza wyświetlanie wartości RGB."""
        self.show_rgb_enabled = not self.show_rgb_enabled
        self.viewer.set_show_rgb(self.show_rgb_enabled)
        if self.show_rgb_enabled:
            self.btn_show_rgb.setText("Pokaż RGB (wyłącz)")
        else:
            self.btn_show_rgb.setText("Pokaż RGB (włącz)")
            
    def load_ppm_file(self):
        """Wczytuje plik PPM."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj plik PPM", "", "PPM Files (*.ppm);;All Files (*)"
        )
        if filename:
            try:
                width, height, max_val, pixels = load_ppm(filename)
                self.image_data = pixels
                self.image_width = width
                self.image_height = height
                self.original_image_data = pixels.copy()
                self.viewer.set_image(pixels, width, height)
                QMessageBox.information(self, "Sukces", f"Wczytano obraz PPM: {width}x{height}")
            except PPMError as e:
                QMessageBox.critical(self, "Błąd PPM", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Nieoczekiwany błąd: {e}")
                
    def load_jpeg_file(self):
        """Wczytuje plik JPEG."""
        if not PIL_AVAILABLE:
            QMessageBox.warning(
                self, "Brak biblioteki",
                "Biblioteka Pillow nie jest zainstalowana.\n"
                "Zainstaluj ją poleceniem: pip install Pillow"
            )
            return
            
        filename, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj plik JPEG", "", "JPEG Files (*.jpg *.jpeg);;All Files (*)"
        )
        if filename:
            try:
                img = Image.open(filename)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                width, height = img.size
                pixels = list(img.getdata())
                
                self.image_data = pixels
                self.image_width = width
                self.image_height = height
                self.original_image_data = pixels.copy()
                self.viewer.set_image(pixels, width, height)
                QMessageBox.information(self, "Sukces", f"Wczytano obraz JPEG: {width}x{height}")
            except Exception as e:
                QMessageBox.critical(self, "Błąd JPEG", f"Błąd podczas wczytywania JPEG: {e}")
                
    def save_jpeg_file(self):
        """Zapisuje obraz jako JPEG."""
        if not PIL_AVAILABLE:
            QMessageBox.warning(
                self, "Brak biblioteki",
                "Biblioteka Pillow nie jest zainstalowana.\n"
                "Zainstaluj ją poleceniem: pip install Pillow"
            )
            return
            
        if self.image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz.")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Zapisz jako JPEG", "", "JPEG Files (*.jpg);;All Files (*)"
        )
        if filename:
            try:
                quality = self.jpeg_quality_slider.value()
                img = Image.new('RGB', (self.image_width, self.image_height))
                img.putdata(self.image_data)
                img.save(filename, 'JPEG', quality=quality)
                QMessageBox.information(self, "Sukces", f"Zapisano obraz jako JPEG (jakość: {quality})")
            except Exception as e:
                QMessageBox.critical(self, "Błąd", f"Błąd podczas zapisywania: {e}")
                
    def apply_averaging(self):
        """Stosuje filtr wygładzający."""
        if self.image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz.")
            return
            
        kernel_size = self.kernel_size_spin.value()
        self.image_data = apply_averaging_filter(
            self.image_data, self.image_width, self.image_height, kernel_size
        )
        self.viewer.set_image(self.image_data, self.image_width, self.image_height)
        
    def apply_median(self):
        """Stosuje filtr medianowy."""
        if self.image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz.")
            return
            
        kernel_size = self.kernel_size_spin.value()
        self.image_data = apply_median_filter(
            self.image_data, self.image_width, self.image_height, kernel_size
        )
        self.viewer.set_image(self.image_data, self.image_width, self.image_height)
        
    def apply_sobel(self):
        """Stosuje filtr Sobel."""
        if self.image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz.")
            return
            
        self.image_data = apply_sobel_filter(
            self.image_data, self.image_width, self.image_height
        )
        self.viewer.set_image(self.image_data, self.image_width, self.image_height)
        
    def convert_to_binary(self):
        """Konwertuje obraz na binarny."""
        if self.image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz.")
            return
            
        self.image_data = rgb_to_binary(self.image_data)
        self.viewer.set_image(self.image_data, self.image_width, self.image_height)
        
    def update_structuring_element(self):
        """Aktualizuje element strukturyzujący z pola tekstowego."""
        try:
            text = self.se_text.toPlainText()
            lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
            se = []
            for line in lines:
                row = [int(x) for x in line.split()]
                se.append(row)
            if len(se) > 0 and all(len(row) == len(se[0]) for row in se):
                self.structuring_element = se
            else:
                # Nie aktualizuj jeśli format jest nieprawidłowy
                pass
        except:
            pass

    def apply_dilation_filter(self):
        """Stosuje dylatację."""
        if self.image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz.")
            return
            
        self.update_structuring_element()
        self.image_data = apply_dilation(
            self.image_data, self.image_width, self.image_height, self.structuring_element
        )
        self.viewer.set_image(self.image_data, self.image_width, self.image_height)
        
    def apply_erosion_filter(self):
        """Stosuje erozję."""
        if self.image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz.")
            return
            
        self.update_structuring_element()
        self.image_data = apply_erosion(
            self.image_data, self.image_width, self.image_height, self.structuring_element
        )
        self.viewer.set_image(self.image_data, self.image_width, self.image_height)
        
    def reset_image(self):
        """Przywraca oryginalny obraz."""
        if self.original_image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Nie wczytano obrazu.")
            return
            
        self.image_data = self.original_image_data.copy()
        self.viewer.set_image(self.image_data, self.image_width, self.image_height)
        
    def scale_colors(self):
        """Stosuje skalowanie liniowe kolorów."""
        if self.image_data is None:
            QMessageBox.warning(self, "Brak obrazu", "Najpierw wczytaj obraz.")
            return
            
        # Znajdź min i max wartości dla każdego kanału
        r_values = [p[0] for p in self.image_data]
        g_values = [p[1] for p in self.image_data]
        b_values = [p[2] for p in self.image_data]
        
        r_min, r_max = min(r_values), max(r_values)
        g_min, g_max = min(g_values), max(g_values)
        b_min, b_max = min(b_values), max(b_values)
        
        # Skaluj liniowo do zakresu 0-255
        scaled = []
        for r, g, b in self.image_data:
            if r_max > r_min:
                r_scaled = int((r - r_min) * 255 / (r_max - r_min))
            else:
                r_scaled = r
            if g_max > g_min:
                g_scaled = int((g - g_min) * 255 / (g_max - g_min))
            else:
                g_scaled = g
            if b_max > b_min:
                b_scaled = int((b - b_min) * 255 / (b_max - b_min))
            else:
                b_scaled = b
            scaled.append((r_scaled, g_scaled, b_scaled))
        
        self.image_data = scaled
        self.viewer.set_image(self.image_data, self.image_width, self.image_height)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
