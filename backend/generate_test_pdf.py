"""
Тестовый скрипт для генерации PDF этикеток.
Запуск: cd backend && .venv/Scripts/python generate_test_pdf.py
"""
import sys
from pathlib import Path

# Добавляем путь к app
sys.path.insert(0, str(Path(__file__).parent))

from app.services.label_generator import LabelGenerator, LabelItem


def main():
    generator = LabelGenerator()

    # Тестовые данные (1 товар) — как на картинке конкурента
    items = [
        LabelItem(
            barcode="1245235243455",
            article='ТутбудетАртикул "БрендОченьКлассный"',
            size="XL",
            color="оранжевый",
            name="Рубашка женская, с пуговицами",
            country="Россия",
            composition="95% хлопок, 5% эластан",
            manufacturer="ООО ХорошийПроизводитель",
            production_date="10.10.25",
        ),
    ]

    # Тестовый код ЧЗ
    codes = [
        "01046037269011112159bDd+4=<j=Lc\x1D93WXYZ",
    ]

    output_dir = Path(__file__).parent.parent / "test"
    output_dir.mkdir(exist_ok=True)

    # Генерируем extended layout 58x40
    pdf_bytes = generator.generate(
        items=items,
        codes=codes,
        size="58x40",
        organization="ООО ХорошийПроизводитель",
        inn="123123123123",
        layout="extended",
        label_format="combined",
        show_article=True,
        show_size_color=True,
        show_name=True,
        show_organization=True,
        show_inn=True,
        show_country=False,
        show_composition=True,  # Показываем состав
        show_chz_code_text=True,
        show_serial_number=True,
        # Адрес для extended шаблона
        organization_address="РФ, г. Москва, Коммунистическая 52-52",
        # Кастомные строки
        custom_lines=["Лишняя строка 1", "Лишняя строка 2", "Лишняя строка 3"],
    )

    output_path = output_dir / "label_extended_58x40.pdf"
    output_path.write_bytes(pdf_bytes)
    print(f"Extended 58x40 сохранён: {output_path}")


if __name__ == "__main__":
    main()
