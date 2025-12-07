"""
Skrypt do tworzenia testowego obrazu PPM do testowania filtrów.
Tworzy obraz z różnymi elementami: tekst, kształty, szum.
"""
from PIL import Image, ImageDraw, ImageFont
import random

def create_test_image_ppm_p3(filename="test_image.ppm", width=400, height=300):
    """Tworzy testowy obraz PPM P3 z różnymi elementami."""
    # Utwórz obraz RGB
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Rysuj prostokąty
    draw.rectangle([50, 50, 150, 100], fill='red', outline='black', width=2)
    draw.rectangle([200, 50, 300, 100], fill='blue', outline='black', width=2)
    draw.rectangle([350, 50, 400, 100], fill='green', outline='black', width=2)
    
    # Rysuj okręgi
    draw.ellipse([50, 120, 150, 220], fill='yellow', outline='black', width=2)
    draw.ellipse([200, 120, 300, 220], fill='magenta', outline='black', width=2)
    
    # Rysuj linie
    for i in range(0, width, 20):
        draw.line([(i, 230), (i+10, 250)], fill='black', width=2)
    
    # Dodaj szum (dla testowania filtrów)
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if random.random() < 0.05:  # 5% pikseli to szum
                pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    # Zapisz jako PPM P3
    with open(filename, 'w') as f:
        f.write('P3\n')
        f.write(f'{width} {height}\n')
        f.write('255\n')
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                f.write(f'{r} {g} {b}\n')
    
    print(f"Utworzono testowy obraz: {filename}")

def create_test_image_ppm_p6(filename="test_image_binary.ppm", width=400, height=300):
    """Tworzy testowy obraz PPM P6 (binarny) do testowania operacji morfologicznych."""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Rysuj czarne kształty na białym tle (dla operacji morfologicznych)
    # Duży prostokąt
    draw.rectangle([50, 50, 200, 150], fill='black')
    
    # Małe prostokąty (szum)
    for i in range(10):
        x = random.randint(250, 350)
        y = random.randint(50, 250)
        size = random.randint(5, 15)
        draw.rectangle([x, y, x+size, y+size], fill='black')
    
    # Okrąg
    draw.ellipse([50, 180, 150, 280], fill='black')
    
    # Zapisz jako PPM P6 (binarny)
    with open(filename, 'wb') as f:
        f.write(b'P6\n')
        f.write(f'{width} {height}\n'.encode())
        f.write(b'255\n')
        pixels = img.load()
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                # Konwertuj na binarny (czarny lub biały)
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                binary = 0 if gray < 128 else 255
                f.write(bytes([binary, binary, binary]))
    
    print(f"Utworzono binarny obraz testowy: {filename}")

if __name__ == "__main__":
    create_test_image_ppm_p3("test_image.ppm")
    create_test_image_ppm_p6("test_image_binary.ppm")
    print("\nObrazy testowe gotowe! Możesz je użyć do testowania filtrów.")

