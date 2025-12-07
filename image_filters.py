"""
Moduł z implementacją filtrów obrazowych.
Wszystkie filtry są zaimplementowane samodzielnie bez użycia bibliotek.
"""
import math


def apply_averaging_filter(image_data, width, height, kernel_size=3):
    """
    Filtr wygładzający (uśredniający).
    
    Args:
        image_data: lista krotek (R, G, B)
        width: szerokość obrazu
        height: wysokość obrazu
        kernel_size: rozmiar jądra (musi być nieparzysty)
        
    Returns:
        lista krotek (R, G, B) - przefiltrowany obraz
    """
    if kernel_size % 2 == 0:
        kernel_size += 1  # Upewnij się, że jest nieparzysty
    
    result = []
    offset = kernel_size // 2
    
    for y in range(height):
        for x in range(width):
            r_sum, g_sum, b_sum = 0, 0, 0
            count = 0
            
            for ky in range(-offset, offset + 1):
                for kx in range(-offset, offset + 1):
                    ny = y + ky
                    nx = x + kx
                    
                    if 0 <= ny < height and 0 <= nx < width:
                        idx = ny * width + nx
                        r, g, b = image_data[idx]
                        r_sum += r
                        g_sum += g
                        b_sum += b
                        count += 1
            
            r_avg = int(r_sum / count)
            g_avg = int(g_sum / count)
            b_avg = int(b_sum / count)
            result.append((r_avg, g_avg, b_avg))
    
    return result


def apply_median_filter(image_data, width, height, kernel_size=3):
    """
    Filtr medianowy.
    
    Args:
        image_data: lista krotek (R, G, B)
        width: szerokość obrazu
        height: wysokość obrazu
        kernel_size: rozmiar jądra (musi być nieparzysty)
        
    Returns:
        lista krotek (R, G, B) - przefiltrowany obraz
    """
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    result = []
    offset = kernel_size // 2
    
    for y in range(height):
        for x in range(width):
            r_values = []
            g_values = []
            b_values = []
            
            for ky in range(-offset, offset + 1):
                for kx in range(-offset, offset + 1):
                    ny = y + ky
                    nx = x + kx
                    
                    if 0 <= ny < height and 0 <= nx < width:
                        idx = ny * width + nx
                        r, g, b = image_data[idx]
                        r_values.append(r)
                        g_values.append(g)
                        b_values.append(b)
            
            r_values.sort()
            g_values.sort()
            b_values.sort()
            
            mid = len(r_values) // 2
            r_median = r_values[mid]
            g_median = g_values[mid]
            b_median = b_values[mid]
            
            result.append((r_median, g_median, b_median))
    
    return result


def apply_sobel_filter(image_data, width, height):
    """
    Filtr wykrywania krawędzi Sobel.
    
    Args:
        image_data: lista krotek (R, G, B)
        width: szerokość obrazu
        height: wysokość obrazu
        
    Returns:
        lista krotek (R, G, B) - obraz z wykrytymi krawędziami
    """
    # Konwertuj na skalę szarości
    gray = []
    for r, g, b in image_data:
        gray_value = int(0.299 * r + 0.587 * g + 0.114 * b)
        gray.append(gray_value)
    
    # Jądra Sobel
    sobel_x = [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ]
    
    sobel_y = [
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1]
    ]
    
    result = []
    
    for y in range(height):
        for x in range(width):
            gx = 0
            gy = 0
            
            for ky in range(-1, 2):
                for kx in range(-1, 2):
                    ny = y + ky
                    nx = x + kx
                    
                    if 0 <= ny < height and 0 <= nx < width:
                        idx = ny * width + nx
                        pixel_value = gray[idx]
                        gx += pixel_value * sobel_x[ky + 1][kx + 1]
                        gy += pixel_value * sobel_y[ky + 1][kx + 1]
            
            # Oblicz magnitudę
            magnitude = int(math.sqrt(gx * gx + gy * gy))
            magnitude = min(255, max(0, magnitude))
            
            result.append((magnitude, magnitude, magnitude))
    
    return result


def rgb_to_binary(image_data, threshold=128):
    """
    Konwertuje obraz RGB na binarny (czarno-biały).
    
    Args:
        image_data: lista krotek (R, G, B)
        threshold: próg binarizacji
        
    Returns:
        lista krotek (R, G, B) - obraz binarny (0 lub 255)
    """
    binary = []
    for r, g, b in image_data:
        gray = int(0.299 * r + 0.587 * g + 0.114 * b)
        value = 255 if gray >= threshold else 0
        binary.append((value, value, value))
    return binary


def apply_dilation(image_data, width, height, structuring_element):
    """
    Dylatacja na obrazie binarnym.
    
    Args:
        image_data: lista krotek (R, G, B) - obraz binarny
        width: szerokość obrazu
        height: wysokość obrazu
        structuring_element: lista list (macierz) elementu strukturyzującego
                             gdzie 1 oznacza aktywny piksel, 0 - nieaktywny
        
    Returns:
        lista krotek (R, G, B) - obraz po dylatacji
    """
    se_height = len(structuring_element)
    se_width = len(structuring_element[0]) if se_height > 0 else 0
    
    se_center_y = se_height // 2
    se_center_x = se_width // 2
    
    result = []
    
    for y in range(height):
        for x in range(width):
            max_value = 0
            
            for se_y in range(se_height):
                for se_x in range(se_width):
                    if structuring_element[se_y][se_x] == 1:
                        img_y = y + se_y - se_center_y
                        img_x = x + se_x - se_center_x
                        
                        if 0 <= img_y < height and 0 <= img_x < width:
                            idx = img_y * width + img_x
                            r, g, b = image_data[idx]
                            max_value = max(max_value, r)  # Dla obrazu binarnego r=g=b
            
            result.append((max_value, max_value, max_value))
    
    return result


def apply_erosion(image_data, width, height, structuring_element):
    """
    Erozja na obrazie binarnym.
    
    Args:
        image_data: lista krotek (R, G, B) - obraz binarny
        width: szerokość obrazu
        height: wysokość obrazu
        structuring_element: lista list (macierz) elementu strukturyzującego
                             gdzie 1 oznacza aktywny piksel, 0 - nieaktywny
        
    Returns:
        lista krotek (R, G, B) - obraz po erozji
    """
    se_height = len(structuring_element)
    se_width = len(structuring_element[0]) if se_height > 0 else 0
    
    se_center_y = se_height // 2
    se_center_x = se_width // 2
    
    result = []
    
    for y in range(height):
        for x in range(width):
            min_value = 255
            
            for se_y in range(se_height):
                for se_x in range(se_width):
                    if structuring_element[se_y][se_x] == 1:
                        img_y = y + se_y - se_center_y
                        img_x = x + se_x - se_center_x
                        
                        if 0 <= img_y < height and 0 <= img_x < width:
                            idx = img_y * width + img_x
                            r, g, b = image_data[idx]
                            min_value = min(min_value, r)  # Dla obrazu binarnego r=g=b
                        else:
                            # Jeśli element strukturyzujący wykracza poza obraz, erozja daje 0
                            min_value = 0
            
            result.append((min_value, min_value, min_value))
    
    return result


