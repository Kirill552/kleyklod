#!/usr/bin/env python3
"""
Скрипт для генерации тестовых файлов: 500 баркодов в Excel + 500 DataMatrix в PDF.
Баркоды и коды ЧЗ перемешаны для проверки GTIN matching.

Использование:
    cd backend
    source .venv/Scripts/activate  # Windows
    python generate_test_500.py
"""

import random
import string
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
from PIL import Image
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# Добавляем путь к app для импорта
sys.path.insert(0, str(Path(__file__).parent))

from app.services.datamatrix import DataMatrixGenerator


def generate_ean13_barcode(base: int, index: int) -> str:
    """Генерирует валидный EAN-13 баркод."""
    # Базовый префикс + индекс
    code_12 = f"{base:07d}{index:05d}"  # 12 цифр без контрольной

    # Расчёт контрольной цифры EAN-13
    odd_sum = sum(int(code_12[i]) for i in range(0, 12, 2))
    even_sum = sum(int(code_12[i]) for i in range(1, 12, 2))
    check = (10 - (odd_sum + even_sum * 3) % 10) % 10

    return code_12 + str(check)


def generate_datamatrix_code(barcode: str, serial_index: int) -> str:
    """Генерирует код маркировки ЧЗ из баркода."""
    # GTIN = "0" + EAN-13 (14 цифр)
    gtin = "0" + barcode

    # Серийный номер (случайные символы, как в реальных кодах)
    serial = "".join(random.choices(string.ascii_letters + string.digits, k=13))

    # Криптохвост (упрощённый, для теста достаточно)
    crypto = "".join(random.choices(string.ascii_letters + string.digits + "+-/", k=40))

    # Формат: 01{GTIN}21{serial}\x1d91{key}\x1d92{crypto}
    # Для теста используем упрощённую версию
    return f"01{gtin}21{serial}\x1d91TEST\x1d92{crypto}"


def create_excel(barcodes: list[tuple[str, dict]], output_path: Path):
    """Создаёт Excel файл с баркодами в формате WB."""
    rows = []
    for i, (barcode, product_info) in enumerate(barcodes):
        rows.append({
            "Номер": i,
            "Категория товара": product_info["category"],
            "Бренд": product_info["brand"],
            "Артикул поставщика": product_info["article"],
            "Артикул цвета": product_info["color_code"],
            "Пол": product_info["gender"],
            "Размер": product_info["size"],
            "Рос. размер": product_info["size"],
            "Штрихкод товара": int(barcode),
            "Розничная цена": product_info["price"],
            "Наименование": product_info["name"],
            "Цвет": product_info["color"],
            "Страна": "Россия",
            "Производитель": "Тестовый производитель",
            "Скидка": "10%",
            "Остаток на складе": 100,
        })

    df = pd.DataFrame(rows)
    df.to_excel(output_path, index=False)
    print(f"Excel создан: {output_path} ({len(rows)} строк)")


def create_pdf_with_datamatrix(codes: list[str], output_path: Path):
    """Создаёт PDF с DataMatrix кодами (по одному на страницу, как в ЧЗ)."""
    # Размер страницы как в реальных файлах ЧЗ (примерно A6)
    page_width = 105 * mm
    page_height = 148 * mm

    c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

    # Инициализируем генератор DataMatrix
    dm_generator = DataMatrixGenerator(target_size_mm=26.0, dpi=203)

    for i, code in enumerate(codes):
        # Генерируем DataMatrix изображение
        result = dm_generator.generate(code)

        if result and result.image:
            # Центрируем DataMatrix на странице
            dm_size = 30 * mm
            x = (page_width - dm_size) / 2
            y = (page_height - dm_size) / 2

            img_buffer = BytesIO()
            result.image.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            c.drawImage(ImageReader(img_buffer), x, y, width=dm_size, height=dm_size)

        # Добавляем номер страницы для отладки
        c.setFont("Helvetica", 8)
        c.drawString(5 * mm, 5 * mm, f"Page {i + 1}")

        if i < len(codes) - 1:
            c.showPage()

        if (i + 1) % 100 == 0:
            print(f"  PDF: создано {i + 1}/{len(codes)} страниц...")

    c.save()
    print(f"PDF создан: {output_path} ({len(codes)} страниц)")


def main():
    # Fix Windows console encoding
    sys.stdout.reconfigure(encoding="utf-8")

    # Конфигурация
    NUM_PRODUCTS = 50  # Уникальных товаров
    CODES_PER_PRODUCT = 10  # Кодов ЧЗ на товар (всего 500)
    BASE_BARCODE = 4670049  # Префикс баркода (как у реального селлера)

    output_dir = Path(__file__).parent.parent / "test" / "500_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Генерация тестовых данных: {NUM_PRODUCTS} товаров x {CODES_PER_PRODUCT} кодов = {NUM_PRODUCTS * CODES_PER_PRODUCT}")
    print(f"Выходная папка: {output_dir}")
    print()

    # Генерируем товары с баркодами
    products = []
    categories = ["Обувь зимняя", "Одежда", "Аксессуары", "Электроника", "Косметика"]
    brands = ["Бренд А", "Бренд Б", "Бренд В", "TestBrand", "Тестовый"]
    colors = ["белый", "чёрный", "красный", "синий", "зелёный"]
    sizes = [36, 38, 40, 42, 44, 46, 48, "S", "M", "L", "XL"]

    for i in range(NUM_PRODUCTS):
        barcode = generate_ean13_barcode(BASE_BARCODE, i)
        product_info = {
            "category": random.choice(categories),
            "brand": random.choice(brands),
            "article": f"ART{i:04d}",
            "color_code": f"C{i % 10}",
            "gender": random.choice(["Мужской", "Женский", "Унисекс", "Детский"]),
            "size": random.choice(sizes),
            "price": random.randint(500, 10000),
            "name": f"Тестовый товар #{i + 1}",
            "color": random.choice(colors),
        }
        products.append((barcode, product_info))

    # Создаём Excel (товары в порядке)
    excel_path = output_dir / "test_500_barcodes.xlsx"
    create_excel(products, excel_path)

    # Генерируем коды ЧЗ (по несколько на товар)
    datamatrix_codes = []
    for barcode, _ in products:
        for j in range(CODES_PER_PRODUCT):
            code = generate_datamatrix_code(barcode, j)
            datamatrix_codes.append((code, barcode))  # Храним связь для проверки

    print(f"\nСгенерировано {len(datamatrix_codes)} кодов ЧЗ")

    # ВАЖНО: Перемешиваем коды для проверки GTIN matching!
    random.shuffle(datamatrix_codes)
    print("Коды перемешаны для проверки GTIN matching")

    # Создаём PDF
    pdf_path = output_dir / "test_500_datamatrix.pdf"
    just_codes = [code for code, _ in datamatrix_codes]
    create_pdf_with_datamatrix(just_codes, pdf_path)

    # Сохраняем маппинг для проверки (опционально)
    mapping_path = output_dir / "mapping.txt"
    with open(mapping_path, "w", encoding="utf-8") as f:
        f.write("# Маппинг: номер страницы -> баркод товара\n")
        for i, (code, barcode) in enumerate(datamatrix_codes):
            gtin = code[2:16]  # Извлекаем GTIN из кода
            f.write(f"Page {i + 1}: GTIN={gtin} -> Barcode={barcode}\n")
    print(f"Маппинг сохранён: {mapping_path}")

    print("\n" + "=" * 50)
    print("ГОТОВО!")
    print(f"Excel: {excel_path}")
    print(f"PDF:   {pdf_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
