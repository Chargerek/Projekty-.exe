"""
Moduł do wczytywania plików PPM (P3 i P6) z wydajnym wczytywaniem blokowym.
"""
import struct
import re


class PPMError(Exception):
    """Wyjątek dla błędów w plikach PPM."""
    pass


def load_ppm_p3(filename):
    """
    Wczytuje plik PPM w formacie P3 (ASCII).
    
    Args:
        filename: ścieżka do pliku
        
    Returns:
        tuple: (width, height, max_value, pixels) gdzie pixels to lista krotek (R, G, B)
    """
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            # Parsuj nagłówek linia po linii
            magic = None
            width = None
            height = None
            max_value = None
            
            # Wczytaj magic number
            while magic is None:
                line = f.readline()
                if not line:
                    raise PPMError("Nieoczekiwany koniec pliku w nagłówku")
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('P3'):
                        magic = 'P3'
                    else:
                        raise PPMError(f"Nieprawidłowy format magic number. Oczekiwano P3, otrzymano: {line[:2]}")
            
            # Wczytaj wymiary
            while width is None or height is None:
                line = f.readline()
                if not line:
                    raise PPMError("Nieoczekiwany koniec pliku w nagłówku")
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        width = int(parts[0])
                        height = int(parts[1])
            
            # Wczytaj max_value
            while max_value is None:
                line = f.readline()
                if not line:
                    raise PPMError("Nieoczekiwany koniec pliku w nagłówku")
                line = line.strip()
                if line and not line.startswith('#'):
                    max_value = int(line)
            
            # Wczytaj dane pikseli - blokowo
            pixels = []
            buffer = f.read()
            # Usuń komentarze
            buffer = re.sub(r'#.*?\n', '\n', buffer)
            # Podziel na liczby
            numbers = re.findall(r'\d+', buffer)
            
            if len(numbers) < width * height * 3:
                raise PPMError(f"Niewystarczająca ilość danych pikseli. Oczekiwano {width * height * 3}, otrzymano {len(numbers)}")
            
            # Konwertuj na piksele
            for i in range(0, width * height * 3, 3):
                r = int(numbers[i])
                g = int(numbers[i + 1])
                b = int(numbers[i + 2])
                # Normalizuj do zakresu 0-255
                if max_value != 255:
                    r = int(r * 255 / max_value)
                    g = int(g * 255 / max_value)
                    b = int(b * 255 / max_value)
                pixels.append((r, g, b))
            
            return width, height, max_value, pixels
            
    except FileNotFoundError:
        raise PPMError(f"Plik nie został znaleziony: {filename}")
    except ValueError as e:
        raise PPMError(f"Błąd parsowania danych: {e}")
    except Exception as e:
        raise PPMError(f"Błąd podczas wczytywania PPM P3: {e}")


def load_ppm_p6(filename):
    """
    Wczytuje plik PPM w formacie P6 (binarny) z wydajnym wczytywaniem blokowym.
    
    Args:
        filename: ścieżka do pliku
        
    Returns:
        tuple: (width, height, max_value, pixels) gdzie pixels to lista krotek (R, G, B)
    """
    try:
        with open(filename, 'rb') as f:
            # Wczytaj nagłówek - linia po linii
            magic = None
            width = None
            height = None
            max_value = None
            
            # Wczytaj magic number
            line = f.readline()
            if not line.startswith(b'P6'):
                raise PPMError(f"Nieprawidłowy format magic number. Oczekiwano P6, otrzymano: {line[:2]}")
            magic = 'P6'
            
            # Wczytaj wymiary
            while width is None or height is None:
                line = f.readline()
                if line.startswith(b'#'):
                    continue
                parts = line.strip().split()
                if len(parts) >= 2:
                    width = int(parts[0])
                    height = int(parts[1])
            
            # Wczytaj max_value
            while max_value is None:
                line = f.readline()
                if line.startswith(b'#'):
                    continue
                max_value = int(line.strip())
            
            # Wczytaj dane pikseli - blokowo (wydajne)
            pixel_count = width * height
            bytes_per_pixel = 3
            total_bytes = pixel_count * bytes_per_pixel
            
            # Wczytaj wszystkie dane naraz (blokowo)
            pixel_data = f.read(total_bytes)
            
            if len(pixel_data) < total_bytes:
                raise PPMError("Niewystarczająca ilość danych pikseli")
            
            # Konwertuj bajty na piksele
            pixels = []
            bytes_per_component = 1 if max_value < 256 else 2
            
            if bytes_per_component == 1:
                # Standardowy przypadek - 1 bajt na komponent
                for i in range(0, len(pixel_data), 3):
                    r = pixel_data[i]
                    g = pixel_data[i + 1]
                    b = pixel_data[i + 2]
                    # Normalizuj jeśli max_value != 255
                    if max_value != 255:
                        r = int(r * 255 / max_value)
                        g = int(g * 255 / max_value)
                        b = int(b * 255 / max_value)
                    pixels.append((r, g, b))
            else:
                # 2 bajty na komponent (max_value > 255)
                for i in range(0, len(pixel_data), 6):
                    r = struct.unpack('>H', pixel_data[i:i+2])[0]
                    g = struct.unpack('>H', pixel_data[i+2:i+4])[0]
                    b = struct.unpack('>H', pixel_data[i+4:i+6])[0]
                    # Normalizuj do 0-255
                    r = int(r * 255 / max_value)
                    g = int(g * 255 / max_value)
                    b = int(b * 255 / max_value)
                    pixels.append((r, g, b))
            
            return width, height, max_value, pixels
            
    except FileNotFoundError:
        raise PPMError(f"Plik nie został znaleziony: {filename}")
    except ValueError as e:
        raise PPMError(f"Błąd parsowania danych: {e}")
    except Exception as e:
        raise PPMError(f"Błąd podczas wczytywania PPM P6: {e}")


def detect_ppm_format(filename):
    """
    Wykrywa format pliku PPM (P3 lub P6).
    
    Returns:
        str: 'P3' lub 'P6' lub None jeśli nie jest PPM
    """
    try:
        with open(filename, 'rb') as f:
            magic = f.read(2)
            if magic == b'P3':
                return 'P3'
            elif magic == b'P6':
                return 'P6'
            return None
    except:
        return None


def load_ppm(filename):
    """
    Automatycznie wykrywa format i wczytuje plik PPM.
    
    Returns:
        tuple: (width, height, max_value, pixels)
    """
    format_type = detect_ppm_format(filename)
    if format_type == 'P3':
        return load_ppm_p3(filename)
    elif format_type == 'P6':
        return load_ppm_p6(filename)
    else:
        raise PPMError(f"Nieobsługiwany format PPM lub plik nie jest plikiem PPM")

