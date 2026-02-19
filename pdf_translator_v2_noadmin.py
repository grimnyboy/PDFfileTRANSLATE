#!/usr/bin/env python3
"""
AutoCAD PDF Translator - Clean Version
Базиран на работещ код с добавени функции за избор на езици и страници
"""
import fitz  # PyMuPDF
from deep_translator import GoogleTranslator
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import time
import os
import sys
import io
from tkinter import Tk, filedialog

# ============================================================================
# АВТОМАТИЧНО НАМИРАНЕ НА TESSERACT И POPPLER В ЛОКАЛНАТА ПАПКА
# ============================================================================

def setup_local_paths():
    """Настройка на локални пътища за Tesseract и Poppler"""
    
    # Текуща директория на скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    tesseract_found = False
    poppler_found = False
    
    # Търсене на Tesseract
    tesseract_paths = [
        os.path.join(script_dir, 'tesseract', 'tesseract.exe'),
        os.path.join(script_dir, 'Tesseract-OCR', 'tesseract.exe'),
        os.path.join(script_dir, 'tesseract-ocr', 'tesseract.exe'),
    ]
    
    for tess_path in tesseract_paths:
        if os.path.exists(tess_path):
            pytesseract.pytesseract.tesseract_cmd = tess_path
            print(f"✅ Tesseract намерен: {tess_path}")
            tesseract_found = True
            break
    
    if not tesseract_found:
        print("⚠️  Tesseract не е намерен в локалната папка")
        choice = input("   Искате ли да изберете Tesseract ръчно? (y/n): ").strip().lower()
        if choice == 'y':
            tess_path = select_tesseract()
            if tess_path:
                pytesseract.pytesseract.tesseract_cmd = tess_path
                print(f"✅ Tesseract избран: {tess_path}")
                tesseract_found = True
    
    # Търсене на Poppler
    poppler_paths = [
        os.path.join(script_dir, 'poppler', 'Library', 'bin'),
        os.path.join(script_dir, 'poppler', 'bin'),
        os.path.join(script_dir, 'poppler-windows', 'Library', 'bin'),
    ]
    
    poppler_path = None
    for pop_path in poppler_paths:
        if os.path.exists(pop_path):
            poppler_path = pop_path
            print(f"✅ Poppler намерен: {pop_path}")
            poppler_found = True
            break
    
    if not poppler_found:
        print("⚠️  Poppler не е намерен в локалната папка")
        choice = input("   Искате ли да изберете Poppler папка ръчно? (y/n): ").strip().lower()
        if choice == 'y':
            poppler_path = select_poppler()
            if poppler_path:
                print(f"✅ Poppler избран: {poppler_path}")
                poppler_found = True
    
    return poppler_path


def select_tesseract():
    """Избор на Tesseract чрез file dialog"""
    print("\n📂 Изберете tesseract.exe файл...")
    try:
        root = Tk()
        root.withdraw()  # Скриване на главния прозорец
        root.attributes('-topmost', True)  # На преден план
        
        file_path = filedialog.askopenfilename(
            title="Изберете tesseract.exe",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")],
            initialdir="C:/Program Files"
        )
        
        root.destroy()
        
        if file_path and os.path.exists(file_path):
            return file_path
        else:
            print("❌ Не е избран валиден файл")
            return None
    except Exception as e:
        print(f"❌ Грешка при избор на файл: {e}")
        return None


def select_poppler():
    """Избор на Poppler bin папка чрез file dialog"""
    print("\n📂 Изберете Poppler bin папка (където са pdfinfo.exe, pdftoppm.exe и др.)...")
    try:
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        folder_path = filedialog.askdirectory(
            title="Изберете Poppler bin папка",
            initialdir="C:/"
        )
        
        root.destroy()
        
        if folder_path and os.path.exists(folder_path):
            # Проверка дали папката съдържа необходимите файлове
            required_files = ['pdfinfo.exe', 'pdftoppm.exe']
            has_files = any(os.path.exists(os.path.join(folder_path, f)) for f in required_files)
            
            if has_files:
                return folder_path
            else:
                print("⚠️  Избраната папка не съдържа Poppler файлове")
                print("   Търсени файлове: pdfinfo.exe, pdftoppm.exe")
                return None
        else:
            print("❌ Не е избрана валидна папка")
            return None
    except Exception as e:
        print(f"❌ Грешка при избор на папка: {e}")
        return None


class AutoCADPDFTranslator:
    def __init__(self, source_lang='bg', target_lang='en', poppler_path=None):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.cache = {}
        self.poppler_path = poppler_path
        
        # Път към Arial шрифт за кирилица (Windows)
        self.font_path = "C:/Windows/Fonts/arial.ttf"
        if not os.path.exists(self.font_path):
            # Опитваме други пътища
            alt_paths = [
                "C:/Windows/Fonts/ArialUni.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "/System/Library/Fonts/Supplemental/Arial.ttf"  # macOS
            ]
            for path in alt_paths:
                if os.path.exists(path):
                    self.font_path = path
                    break
            else:
                self.font_path = None
        
    def translate_text(self, text):
        """Превод на текст с кеширане"""
        if not text or len(text.strip()) < 2:
            return text
        
        text = text.strip()
        
        # Пропускане на числа и символи
        if text.replace('.', '').replace(',', '').replace('-', '').replace('/', '').isdigit():
            return text
        
        if text in self.cache:
            return self.cache[text]
        
        try:
            time.sleep(0.3)
            translated = GoogleTranslator(source=self.source_lang, target=self.target_lang).translate(text)
            self.cache[text] = translated
            print(f"  ✓ {text[:40]} → {translated[:40]}")
            return translated
        except Exception:
            return text
    
    def detect_text_method(self, pdf_path):
        """Определя дали PDF има текстов слой"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            text = page.get_text()
            doc.close()
            return len(text.strip()) > 50
        except:
            return False
    
    def translate_pdf_with_text_layer(self, input_path, output_path, pages_to_process=None):
        """Превод на PDF с текстов слой"""
        print("\n📝 Обработка на текстов слой...")
        
        try:
            doc = fitz.open(input_path)
            total_pages = len(doc)
            target_pages = pages_to_process if pages_to_process else range(total_pages)
            
            for page_num in target_pages:
                if page_num >= total_pages:
                    continue
                
                print(f"Обработка на страница {page_num + 1}/{total_pages}")
                page = doc[page_num]
                text_instances = page.get_text("dict", flags=11)
                
                for block in text_instances["blocks"]:
                    if block["type"] == 0:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                original = span["text"].strip()
                                if not original or len(original) < 2:
                                    continue
                                
                                translated = self.translate_text(original)
                                
                                if translated != original:
                                    bbox = list(span["bbox"])
                                    rect = fitz.Rect(bbox)
                                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                                    
                                    scale = len(original) / max(len(translated), 1)
                                    new_fontsize = span["size"] * min(scale, 0.95)
                                    
                                    # Вмъкване с Arial шрифт
                                    # Началната точка и ротацията зависят от ротацията на страницата
                                    page_rotation = page.rotation
                                    if page_rotation == 270:
                                        insert_pt = (bbox[0], bbox[1])
                                        insert_rotate = 270
                                    elif page_rotation == 90:
                                        insert_pt = (bbox[2], bbox[3])
                                        insert_rotate = 90
                                    elif page_rotation == 180:
                                        insert_pt = (bbox[2], bbox[3] - 2)
                                        insert_rotate = 180
                                    else:  # 0 - нормална страница
                                        insert_pt = (bbox[0], bbox[3] - 2)
                                        insert_rotate = 0
                                    page.insert_text(
                                        insert_pt,
                                        translated,
                                        fontsize=new_fontsize,
                                        color=(0, 0, 0),
                                        fontname="arial",
                                        fontfile=self.font_path,
                                        rotate=insert_rotate
                                    )
            
            doc.save(output_path, garbage=4, deflate=True)
            doc.close()
            return True
            
        except Exception as e:
            print(f"Грешка при запис: {e}")
            return False
    
    def translate_pdf_with_ocr(self, input_path, output_path, pages_to_process=None):
        """Превод на сканиран PDF с OCR"""
        print("\n🔍 OCR обработка...")
        
        try:
            first = pages_to_process[0] + 1 if pages_to_process else None
            last = pages_to_process[-1] + 1 if pages_to_process else None
            
            if self.poppler_path:
                images = convert_from_path(input_path, dpi=300, first_page=first, last_page=last, poppler_path=self.poppler_path)
            else:
                images = convert_from_path(input_path, dpi=300, first_page=first, last_page=last)
            
            original_doc = fitz.open(input_path)
            new_doc = fitz.open()
            
            # Определяне кой OCR език да се използва
            ocr_lang = 'bul+eng' if self.source_lang == 'bg' else 'eng'
            
            for i, image in enumerate(images):
                curr_page_num = pages_to_process[i] if pages_to_process else i
                print(f"OCR Страница {curr_page_num + 1}")
                
                data = pytesseract.image_to_data(image, lang=ocr_lang, output_type=pytesseract.Output.DICT)
                
                orig_page = original_doc[curr_page_num]
                page_rect = orig_page.rect
                new_page = new_doc.new_page(width=page_rect.width, height=page_rect.height)
                
                img_bytes = io.BytesIO()
                image.save(img_bytes, format='PNG')
                new_page.insert_image(page_rect, stream=img_bytes.getvalue())
                
                scale_x = page_rect.width / image.width
                scale_y = page_rect.height / image.height
                
                for j in range(len(data['text'])):
                    txt = data['text'][j].strip()
                    if txt and len(txt) > 1 and int(data['conf'][j]) > 30:
                        translated = self.translate_text(txt)
                        if translated != txt:
                            x0 = data['left'][j] * scale_x
                            y0 = data['top'][j] * scale_y
                            x1 = (data['left'][j] + data['width'][j]) * scale_x
                            y1 = (data['top'][j] + data['height'][j]) * scale_y
                            
                            new_page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=(1, 1, 1), fill=(1, 1, 1))
                            new_page.insert_text(
                                (x0, y1 - 2),
                                translated,
                                fontsize=(y1 - y0) * 0.8,
                                color=(0, 0, 0),
                                fontname="arial",
                                fontfile=self.font_path
                            )
            
            original_doc.close()
            new_doc.save(output_path, garbage=4, deflate=True)
            new_doc.close()
            return True
            
        except Exception as e:
            print(f"Грешка при OCR: {e}")
            return False

    def translate_pdf(self, input_path, output_path, pages_to_process=None):
        """Главна функция за превод"""
        if not os.path.exists(input_path):
            return False
        
        if self.detect_text_method(input_path):
            return self.translate_pdf_with_text_layer(input_path, output_path, pages_to_process)
        else:
            return self.translate_pdf_with_ocr(input_path, output_path, pages_to_process)


def main():
    """Главна функция"""
    print("\n" + "="*70)
    print("AUTOCAD PDF ПРЕВОДАЧ")
    print("="*70)
    
    # Настройка на локални пътища
    poppler_path = setup_local_paths()
    
    # ========================================================================
    # ИЗБОР НА ЕЗИЦИ
    # ========================================================================
    print("\n" + "="*70)
    print("ИЗБОР НА ЕЗИЦИ")
    print("="*70)
    
    languages = {
        '1': ('bg', 'en', 'Български → English'),
        '2': ('en', 'bg', 'English → Български'),
        '3': ('bg', 'ru', 'Български → Русский'),
        '4': ('ru', 'bg', 'Русский → Български'),
        '5': ('en', 'de', 'English → Deutsch'),
        '6': ('en', 'fr', 'English → Français'),
        '7': ('bg', 'de', 'Български → Deutsch'),
    }
    
    print("\nНай-чести комбинации:")
    for key, (src, tgt, desc) in languages.items():
        print(f"  {key}. {desc}")
    print(f"  8. Друга комбинация")
    
    lang_choice = input("\n👉 Избор (по подразбиране 1): ").strip()
    
    if not lang_choice or lang_choice == '1':
        source_lang, target_lang = 'bg', 'en'
    elif lang_choice in languages:
        source_lang, target_lang = languages[lang_choice][0], languages[lang_choice][1]
    elif lang_choice == '8':
        source_lang = input("  От език (bg): ").strip().lower() or 'bg'
        target_lang = input("  На език (en): ").strip().lower() or 'en'
    else:
        source_lang, target_lang = 'bg', 'en'
    
    print(f"\n✓ Избрани езици: {source_lang} → {target_lang}")
    
    # ========================================================================
    # ИЗБОР НА PDF ФАЙЛ
    # ========================================================================
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf') and not f.endswith('_TR.pdf')]
    
    if not pdf_files:
        print("\n❌ Няма PDF файлове.")
        return
    
    print(f"\n📁 Намерени PDF файлове:")
    for i, f in enumerate(pdf_files, 1):
        size_mb = os.path.getsize(f) / (1024 * 1024)
        print(f"  {i}. {f} ({size_mb:.2f} MB)")
    
    choice = input("\n👉 Изберете файл №: ").strip()
    input_file = pdf_files[int(choice) - 1] if choice else pdf_files[0]
    
    # ========================================================================
    # ИЗБОР НА СТРАНИЦИ
    # ========================================================================
    doc = fitz.open(input_file)
    total = len(doc)
    doc.close()
    
    print(f"\n📄 Общо страници: {total}")
    print("Опции:")
    print("  • Enter - всички страници")
    print("  • '5' - само страница 5")
    print("  • '1-10' - страници от 1 до 10")
    
    pages_input = input(f"\n👉 Страници (Enter за всички): ").strip()
    pages_to_process = None
    
    if pages_input:
        try:
            if '-' in pages_input:
                start, end = map(int, pages_input.split('-'))
                pages_to_process = list(range(start - 1, end))
            else:
                pages_to_process = [int(pages_input) - 1]
        except:
            print("⚠️  Невалиден формат, ще се преведат всички страници")
            pages_to_process = None
    
    # ========================================================================
    # ИМЕ НА ИЗХОДНИЯ ФАЙЛ
    # ========================================================================
    suffix_map = {
        'en': '_EN',
        'bg': '_BG',
        'ru': '_RU',
        'de': '_DE',
        'fr': '_FR',
    }
    suffix = suffix_map.get(target_lang, '_TR')
    output_file = input_file.replace(".pdf", f"{suffix}.pdf")
    
    print(f"\n📝 Изходен файл: {output_file}")
    
    # ========================================================================
    # ПРЕВОД
    # ========================================================================
    translator = AutoCADPDFTranslator(
        source_lang=source_lang,
        target_lang=target_lang,
        poppler_path=poppler_path
    )
    
    if translator.translate_pdf(input_file, output_file, pages_to_process):
        print(f"\n{'='*70}")
        print(f"✅ УСПЕХ! Файлът е създаден:")
        print(f"   {os.path.abspath(output_file)}")
        print(f"{'='*70}")
        print(f"\n📊 Статистика:")
        print(f"  • Преведени фрази: {len(translator.cache)}")
        if pages_to_process:
            print(f"  • Преведени страници: {len(pages_to_process)}")
    else:
        print("\n❌ Файлът не беше създаден поради грешка.")


if __name__ == "__main__":
    main()
