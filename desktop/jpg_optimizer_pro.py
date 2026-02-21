#!/usr/bin/env python3
"""
JPG Optimizer Pro - Професійна оптимізація JPG зображень
Режими: Lossless, Balanced, Maximum Compression
Функції: Порівняння до/після з магніфаєром, вибір папки збереження, шаблони імен
"""

import os
import sys
import shutil
import subprocess
import threading
import tempfile
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple, List

# Check and install required packages
def check_dependencies():
    required = ['PIL', 'piexif']
    missing = []

    try:
        from PIL import Image, ImageTk, ImageFilter, ImageEnhance
        import piexif
    except ImportError as e:
        print(f"Встановлюю необхідні пакети...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "piexif", "-q"])

check_dependencies()

from PIL import Image, ImageTk, ImageFilter, ImageEnhance
import piexif

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText


def setup_theme(root):
    """Configure theme for better visibility on macOS dark mode"""
    style = ttk.Style()

    # Try to use a native theme
    available_themes = style.theme_names()
    if 'aqua' in available_themes:
        style.theme_use('aqua')
    elif 'clam' in available_themes:
        style.theme_use('clam')

    # Configure colors for dark mode compatibility
    bg_color = '#f0f0f0'
    fg_color = '#000000'

    # Check if dark mode (macOS)
    try:
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
            capture_output=True, text=True
        )
        if 'Dark' in result.stdout:
            bg_color = '#2d2d2d'
            fg_color = '#ffffff'
    except:
        pass

    # Configure root window
    root.configure(bg=bg_color)

    # Configure ttk styles
    style.configure('TFrame', background=bg_color)
    style.configure('TLabel', background=bg_color, foreground=fg_color)
    style.configure('TLabelframe', background=bg_color)
    style.configure('TLabelframe.Label', background=bg_color, foreground=fg_color)
    style.configure('TButton', padding=6)
    style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
    style.configure('TRadiobutton', background=bg_color, foreground=fg_color)
    style.configure('TNotebook', background=bg_color)
    style.configure('TNotebook.Tab', padding=[10, 5])

    return bg_color, fg_color


class NavigatorCompareWindow(tk.Toplevel):
    """Вікно порівняння до/після з навігатором як у Photoshop"""

    def __init__(self, parent, original_path: str, optimized_path: str):
        super().__init__(parent)
        self.title("Порівняння: До / Після")
        self.geometry("1300x800")
        self.minsize(1000, 700)

        self.original_path = original_path
        self.optimized_path = optimized_path

        # Load images
        self.original_img = Image.open(original_path)
        self.optimized_img = Image.open(optimized_path)

        # Navigator state
        self.nav_view_x = 0.5  # Center position (0-1)
        self.nav_view_y = 0.5
        self.zoom_level = 4  # Magnification level for detail views

        self.setup_ui()
        self.bind_events()
        self.update_all()

    def setup_ui(self):
        # Configure window background
        self.configure(bg='#f0f0f0')

        # Top info bar
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        orig_size = os.path.getsize(self.original_path)
        opt_size = os.path.getsize(self.optimized_path)
        saved = orig_size - opt_size
        saved_percent = (saved / orig_size * 100) if orig_size > 0 else 0

        ttk.Label(info_frame, text=f"📄 {os.path.basename(self.original_path)}", font=("SF Pro Display", 12, "bold")).pack(side=tk.LEFT)
        ttk.Label(info_frame, text=f"   |   Оригінал: {self.format_size(orig_size)} → Після: {self.format_size(opt_size)}   |   ", font=("SF Pro Display", 11)).pack(side=tk.LEFT)
        ttk.Label(info_frame, text=f"💾 Зекономлено: {self.format_size(saved)} ({saved_percent:.1f}%)", font=("SF Pro Display", 11, "bold"), foreground="green").pack(side=tk.LEFT)

        # Zoom controls
        zoom_frame = ttk.Frame(info_frame)
        zoom_frame.pack(side=tk.RIGHT)

        ttk.Label(zoom_frame, text="Збільшення:").pack(side=tk.LEFT, padx=(0, 5))
        self.zoom_var = tk.IntVar(value=4)
        zoom_values = [("2x", 2), ("4x", 4), ("6x", 6), ("8x", 8)]
        for text, val in zoom_values:
            ttk.Radiobutton(zoom_frame, text=text, value=val, variable=self.zoom_var, command=self.update_all).pack(side=tk.LEFT, padx=2)

        # Main content area
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left side: Navigator (thumbnail with red rectangle)
        nav_frame = ttk.LabelFrame(main_frame, text="🗺 Навігатор - рухайте мишкою", padding=5)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Navigator canvas - shows thumbnail
        self.nav_size = 250
        self.nav_canvas = tk.Canvas(nav_frame, width=self.nav_size, height=self.nav_size, bg='#1a1a1a', highlightthickness=1, highlightbackground='#444')
        self.nav_canvas.pack(pady=5)

        # Position info
        self.pos_label = ttk.Label(nav_frame, text="Позиція: центр")
        self.pos_label.pack(pady=5)

        # Instructions
        ttk.Label(nav_frame, text="Рухайте мишкою по\nзображенню-навігатору\nщоб переглядати деталі", foreground="gray", justify=tk.CENTER).pack(pady=10)

        # Right side: Detail views (Before / After)
        detail_frame = ttk.Frame(main_frame)
        detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Detail view size
        self.detail_size = 400

        # Before panel
        before_frame = ttk.LabelFrame(detail_frame, text="🔍 Оригінал (До)", padding=5)
        before_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.before_canvas = tk.Canvas(before_frame, bg='#1a1a1a', highlightthickness=1, highlightbackground='#666')
        self.before_canvas.pack(fill=tk.BOTH, expand=True)

        # After panel
        after_frame = ttk.LabelFrame(detail_frame, text="🔍 Оптимізовано (Після)", padding=5)
        after_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.after_canvas = tk.Canvas(after_frame, bg='#1a1a1a', highlightthickness=1, highlightbackground='#666')
        self.after_canvas.pack(fill=tk.BOTH, expand=True)

        # Bottom controls
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(bottom_frame, text="💡 Порада: шукайте відмінності в дрібних деталях, тексті та краях об'єктів", foreground="gray").pack(side=tk.LEFT)
        ttk.Button(bottom_frame, text="Закрити", command=self.destroy).pack(side=tk.RIGHT)

    def bind_events(self):
        # Navigator mouse events
        self.nav_canvas.bind("<Motion>", self.on_nav_move)
        self.nav_canvas.bind("<Leave>", self.on_nav_leave)

        # Update on resize
        self.before_canvas.bind("<Configure>", lambda e: self.update_detail_views())
        self.after_canvas.bind("<Configure>", lambda e: self.update_detail_views())

    def update_all(self):
        """Update navigator thumbnail and detail views"""
        self.update_navigator()
        self.update_detail_views()

    def update_navigator(self):
        """Draw thumbnail in navigator with view rectangle"""
        # Create thumbnail
        img_w, img_h = self.original_img.size
        scale = min(self.nav_size / img_w, self.nav_size / img_h)
        thumb_w = int(img_w * scale)
        thumb_h = int(img_h * scale)

        thumbnail = self.original_img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        self.nav_photo = ImageTk.PhotoImage(thumbnail)

        # Clear and draw
        self.nav_canvas.delete("all")

        # Center thumbnail
        x_offset = (self.nav_size - thumb_w) // 2
        y_offset = (self.nav_size - thumb_h) // 2
        self.nav_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=self.nav_photo)

        # Store for coordinate conversion
        self.thumb_offset = (x_offset, y_offset)
        self.thumb_size = (thumb_w, thumb_h)
        self.thumb_scale = scale

        # Draw view rectangle (red rectangle showing current view area)
        self.draw_view_rectangle()

    def draw_view_rectangle(self):
        """Draw red rectangle showing current view area on navigator"""
        self.nav_canvas.delete("view_rect")

        if not hasattr(self, 'thumb_scale'):
            return

        zoom = self.zoom_var.get()
        img_w, img_h = self.original_img.size

        # Calculate view size in original image coordinates
        # This is the area we're zooming into
        view_w = 200 / zoom  # Approximate view area
        view_h = 200 / zoom

        # Current center position
        center_x = self.nav_view_x * img_w
        center_y = self.nav_view_y * img_h

        # View rectangle bounds
        left = center_x - view_w / 2
        top = center_y - view_h / 2
        right = center_x + view_w / 2
        bottom = center_y + view_h / 2

        # Convert to thumbnail coordinates
        x_off, y_off = self.thumb_offset
        rect_left = x_off + left * self.thumb_scale
        rect_top = y_off + top * self.thumb_scale
        rect_right = x_off + right * self.thumb_scale
        rect_bottom = y_off + bottom * self.thumb_scale

        # Draw rectangle
        self.nav_canvas.create_rectangle(
            rect_left, rect_top, rect_right, rect_bottom,
            outline='red', width=2, tags="view_rect"
        )

    def on_nav_move(self, event):
        """Handle mouse movement over navigator"""
        if not hasattr(self, 'thumb_offset'):
            return

        x_off, y_off = self.thumb_offset
        thumb_w, thumb_h = self.thumb_size

        # Convert mouse position to image coordinates (0-1)
        rel_x = (event.x - x_off) / thumb_w
        rel_y = (event.y - y_off) / thumb_h

        # Clamp to valid range
        rel_x = max(0, min(1, rel_x))
        rel_y = max(0, min(1, rel_y))

        self.nav_view_x = rel_x
        self.nav_view_y = rel_y

        # Update position label
        img_w, img_h = self.original_img.size
        px = int(rel_x * img_w)
        py = int(rel_y * img_h)
        self.pos_label.config(text=f"Позиція: {px}, {py}")

        # Update views
        self.draw_view_rectangle()
        self.update_detail_views()

    def on_nav_leave(self, event):
        """Handle mouse leaving navigator"""
        pass  # Keep current view

    def update_detail_views(self):
        """Update before/after detail views"""
        zoom = self.zoom_var.get()
        img_w, img_h = self.original_img.size

        # Calculate crop region
        center_x = int(self.nav_view_x * img_w)
        center_y = int(self.nav_view_y * img_h)

        # Get canvas size
        try:
            canvas_w = self.before_canvas.winfo_width()
            canvas_h = self.before_canvas.winfo_height()
            if canvas_w < 10 or canvas_h < 10:
                canvas_w = canvas_h = 400
        except:
            canvas_w = canvas_h = 400

        # Crop size based on zoom
        crop_w = canvas_w // zoom
        crop_h = canvas_h // zoom

        # Crop bounds
        left = max(0, center_x - crop_w // 2)
        top = max(0, center_y - crop_h // 2)
        right = min(img_w, left + crop_w)
        bottom = min(img_h, top + crop_h)

        # Adjust if at edges
        if right - left < crop_w and left > 0:
            left = max(0, right - crop_w)
        if bottom - top < crop_h and top > 0:
            top = max(0, bottom - crop_h)

        # Crop and resize for both images
        before_crop = self.original_img.crop((left, top, right, bottom))
        after_crop = self.optimized_img.crop((left, top, right, bottom))

        # Resize to canvas size
        before_resized = before_crop.resize((canvas_w, canvas_h), Image.Resampling.NEAREST)  # NEAREST to see pixels
        after_resized = after_crop.resize((canvas_w, canvas_h), Image.Resampling.NEAREST)

        # Convert to PhotoImage
        self.before_photo = ImageTk.PhotoImage(before_resized)
        self.after_photo = ImageTk.PhotoImage(after_resized)

        # Draw on canvases
        self.before_canvas.delete("all")
        self.after_canvas.delete("all")

        self.before_canvas.create_image(canvas_w // 2, canvas_h // 2, image=self.before_photo)
        self.after_canvas.create_image(canvas_w // 2, canvas_h // 2, image=self.after_photo)

    def format_size(self, bytes_size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} ТБ"


class JPGOptimizerPro:
    """Main application class"""

    # Optimization modes
    MODE_LOSSLESS = "lossless"
    MODE_BALANCED = "balanced"
    MODE_MAXIMUM = "maximum"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JPG Optimizer Pro")
        self.root.geometry("750x850")
        self.root.minsize(650, 750)

        # Setup theme for dark mode compatibility
        self.bg_color, self.fg_color = setup_theme(self.root)

        # State
        self.selected_paths: List[str] = []
        self.output_folder: Optional[str] = None
        self.is_processing = False
        self.processed_files: List[Tuple[str, str]] = []  # (original, optimized)

        # Variables
        self.mode = tk.StringVar(value=self.MODE_BALANCED)
        self.quality = tk.IntVar(value=85)
        self.remove_metadata = tk.BooleanVar(value=False)
        self.preserve_subfolders = tk.BooleanVar(value=True)
        self.overwrite_original = tk.BooleanVar(value=False)
        self.use_mozjpeg = tk.BooleanVar(value=True)  # MozJPEG toggle

        # Naming template
        self.naming_template = tk.StringVar(value="{name}_optimized")
        self.naming_options = [
            ("{name}", "Оригінальне ім'я (перезаписати)"),
            ("{name}_optimized", "Додати _optimized"),
            ("{name}_opt_{date}", "Ім'я + дата"),
            ("{date}_{name}", "Дата + ім'я"),
            ("optimized_{counter}_{name}", "Нумерація + ім'я"),
        ]

        # Stats
        self.total_original = 0
        self.total_saved = 0
        self.processed_count = 0
        self.total_count = 0
        self.file_counter = 0
        self._counter_lock = threading.Lock()

        # Check for jpegtran (for lossless mode)
        self.has_jpegtran = self.check_jpegtran()
        self.has_mozjpeg = self.check_mozjpeg()

        self.setup_ui()

    def check_jpegtran(self) -> bool:
        """Check if jpegtran is available (prefer MozJPEG version)"""
        # Check MozJPEG jpegtran first (better optimization)
        mozjpeg_paths = ["/opt/homebrew/opt/mozjpeg/bin/jpegtran", "/usr/local/opt/mozjpeg/bin/jpegtran"]
        for path in mozjpeg_paths:
            if os.path.exists(path):
                self.jpegtran_path = path
                return True
        # Fallback to system jpegtran
        try:
            result = subprocess.run(["jpegtran", "-version"], capture_output=True, timeout=5)
            self.jpegtran_path = "jpegtran"
            return True
        except:
            self.jpegtran_path = None
            return False

    def check_mozjpeg(self) -> bool:
        """Check if MozJPEG cjpeg is available"""
        try:
            # Check common MozJPEG locations on macOS
            paths = ["/opt/homebrew/opt/mozjpeg/bin/cjpeg", "/usr/local/opt/mozjpeg/bin/cjpeg"]
            for path in paths:
                if os.path.exists(path):
                    self.mozjpeg_path = path
                    return True
            return False
        except:
            return False

    def setup_ui(self):
        # Main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Main
        main_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(main_tab, text="📷 Оптимізація")

        # Tab 2: Settings
        settings_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(settings_tab, text="⚙️ Налаштування")

        self.setup_main_tab(main_tab)
        self.setup_settings_tab(settings_tab)

    def setup_main_tab(self, parent):
        # Header
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(header, text="JPG Optimizer Pro", font=("SF Pro Display", 24, "bold")).pack(side=tk.LEFT)

        # Mode selection
        mode_frame = ttk.LabelFrame(parent, text="Режим оптимізації", padding=10)
        mode_frame.pack(fill=tk.X, pady=(0, 15))

        modes = [
            (self.MODE_LOSSLESS, "🔒 Lossless", "Без втрат якості. Оптимізація Huffman таблиць, видалення зайвих даних."),
            (self.MODE_BALANCED, "⚖️ Balanced", "Баланс якості та розміру. Налаштовуваний рівень стиснення."),
            (self.MODE_MAXIMUM, "📦 Maximum", "Максимальне стиснення. Для веб та економії місця."),
        ]

        for value, text, desc in modes:
            frame = ttk.Frame(mode_frame)
            frame.pack(fill=tk.X, pady=2)

            rb = ttk.Radiobutton(frame, text=text, value=value, variable=self.mode, command=self.on_mode_change)
            rb.pack(side=tk.LEFT)

            ttk.Label(frame, text=desc, foreground="gray").pack(side=tk.LEFT, padx=(10, 0))

        # Quality slider (for balanced mode)
        self.quality_frame = ttk.Frame(mode_frame)
        self.quality_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(self.quality_frame, text="Якість:").pack(side=tk.LEFT)
        self.quality_label = ttk.Label(self.quality_frame, text="85%", width=5)
        self.quality_label.pack(side=tk.RIGHT)

        self.quality_slider = ttk.Scale(
            self.quality_frame, from_=60, to=100, orient=tk.HORIZONTAL,
            variable=self.quality, command=self.update_quality_label
        )
        self.quality_slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)

        # MozJPEG toggle
        if self.has_mozjpeg:
            mozjpeg_frame = ttk.Frame(mode_frame)
            mozjpeg_frame.pack(fill=tk.X, pady=(10, 0))

            ttk.Checkbutton(
                mozjpeg_frame,
                text="🚀 Використовувати MozJPEG (краща якість при меншому розмірі)",
                variable=self.use_mozjpeg
            ).pack(side=tk.LEFT)

            self.mozjpeg_status = ttk.Label(mozjpeg_frame, text="✅ Активний", foreground="green")
            self.mozjpeg_status.pack(side=tk.RIGHT)

            # Update status when toggled
            self.use_mozjpeg.trace_add("write", self._update_mozjpeg_status)
        elif not self.has_jpegtran:
            ttk.Label(mode_frame, text="⚠️ MozJPEG не знайдено. Використовується Pillow.", foreground="orange").pack(anchor=tk.W, pady=(5, 0))

        # File selection
        files_frame = ttk.LabelFrame(parent, text="Файли для оптимізації", padding=10)
        files_frame.pack(fill=tk.X, pady=(0, 15))

        # File list
        list_frame = ttk.Frame(files_frame)
        list_frame.pack(fill=tk.X)

        self.file_listbox = tk.Listbox(
            list_frame, height=5, font=("SF Pro Display", 11), selectmode=tk.EXTENDED,
            bg='white', fg='black', selectbackground='#0066cc', selectforeground='white'
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # File buttons
        btn_frame = ttk.Frame(files_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="📁 Додати файли", command=self.select_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="📂 Додати папку", command=self.select_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🗑 Видалити вибрані", command=self.remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="❌ Очистити все", command=self.clear_selection).pack(side=tk.LEFT)

        self.file_count_label = ttk.Label(btn_frame, text="Файлів: 0")
        self.file_count_label.pack(side=tk.RIGHT)

        # Output settings
        output_frame = ttk.LabelFrame(parent, text="Збереження", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 15))

        # Output folder
        folder_row = ttk.Frame(output_frame)
        folder_row.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(folder_row, text="Папка:").pack(side=tk.LEFT)
        self.output_label = ttk.Label(folder_row, text="(та сама папка, що й оригінал)", foreground="gray")
        self.output_label.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Button(folder_row, text="Вибрати папку", command=self.select_output_folder).pack(side=tk.RIGHT)
        ttk.Button(folder_row, text="Скинути", command=self.reset_output_folder).pack(side=tk.RIGHT, padx=(0, 5))

        # Naming template
        naming_row = ttk.Frame(output_frame)
        naming_row.pack(fill=tk.X)

        ttk.Label(naming_row, text="Шаблон імені:").pack(side=tk.LEFT)

        self.naming_combo = ttk.Combobox(naming_row, textvariable=self.naming_template, width=30)
        self.naming_combo['values'] = [opt[0] for opt in self.naming_options]
        self.naming_combo.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(naming_row, text="Змінні: {name}, {date}, {counter}", foreground="gray", font=("SF Pro Display", 10)).pack(side=tk.LEFT, padx=(10, 0))

        # Progress
        progress_frame = ttk.LabelFrame(parent, text="Прогрес", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="Готовий до оптимізації")
        self.progress_label.pack()

        # Results
        results_frame = ttk.LabelFrame(parent, text="Результати", padding=10)
        results_frame.pack(fill=tk.X, pady=(0, 15))

        results_grid = ttk.Frame(results_frame)
        results_grid.pack(fill=tk.X)

        for col, (label, var_name) in enumerate([
            ("📄 Оригінал:", "original_label"),
            ("📦 Після:", "new_label"),
            ("💾 Зекономлено:", "saved_label"),
            ("📊 Відсоток:", "percent_label")
        ]):
            ttk.Label(results_grid, text=label).grid(row=0, column=col*2, sticky=tk.W, padx=(0, 5))
            lbl = ttk.Label(results_grid, text="—", font=("SF Pro Display", 11, "bold"))
            lbl.grid(row=0, column=col*2+1, sticky=tk.W, padx=(0, 20))
            setattr(self, var_name, lbl)

        # Log
        log_frame = ttk.LabelFrame(parent, text="Журнал", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.log_text = ScrolledText(
            log_frame, height=6, font=("SF Mono", 10), state=tk.DISABLED,
            bg='white', fg='black'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Actions
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X)

        ttk.Button(action_frame, text="🔍 Порівняти до/після", command=self.show_comparison).pack(side=tk.LEFT)

        self.optimize_btn = ttk.Button(action_frame, text="🚀 Оптимізувати", command=self.start_optimization)
        self.optimize_btn.pack(side=tk.RIGHT)

    def setup_settings_tab(self, parent):
        # Metadata
        meta_frame = ttk.LabelFrame(parent, text="Метадані", padding=10)
        meta_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Checkbutton(meta_frame, text="Видалити EXIF метадані (дата, GPS, камера)", variable=self.remove_metadata).pack(anchor=tk.W)
        ttk.Label(meta_frame, text="Видалення метаданих зменшує розмір, але втрачає інформацію про фото.", foreground="gray").pack(anchor=tk.W, pady=(5, 0))
        ttk.Label(meta_frame, text="🎨 ICC кольоровий профіль зберігається завжди для точної передачі кольорів.", foreground="gray").pack(anchor=tk.W, pady=(2, 0))

        # Folder structure
        folder_frame = ttk.LabelFrame(parent, text="Структура папок", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Checkbutton(folder_frame, text="Зберігати структуру підпапок при виборі папки", variable=self.preserve_subfolders).pack(anchor=tk.W)

        # Overwrite
        overwrite_frame = ttk.LabelFrame(parent, text="Перезапис", padding=10)
        overwrite_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Checkbutton(overwrite_frame, text="Перезаписувати оригінальні файли (без створення нових)", variable=self.overwrite_original).pack(anchor=tk.W)
        ttk.Label(overwrite_frame, text="⚠️ Увага: оригінальні файли будуть замінені!", foreground="red").pack(anchor=tk.W, pady=(5, 0))

        # Tool info
        tools_frame = ttk.LabelFrame(parent, text="Встановлені інструменти", padding=10)
        tools_frame.pack(fill=tk.X, pady=(0, 15))

        jpegtran_status = "✅ Встановлено" if self.has_jpegtran else "❌ Не знайдено"
        mozjpeg_status = "✅ Встановлено" if self.has_mozjpeg else "❌ Не знайдено"

        ttk.Label(tools_frame, text=f"jpegtran: {jpegtran_status}").pack(anchor=tk.W)
        ttk.Label(tools_frame, text=f"MozJPEG: {mozjpeg_status}").pack(anchor=tk.W)

        if not self.has_jpegtran or not self.has_mozjpeg:
            ttk.Label(tools_frame, text="\nДля кращих результатів встановіть MozJPEG:", foreground="gray").pack(anchor=tk.W, pady=(10, 0))
            ttk.Label(tools_frame, text="brew install mozjpeg", font=("SF Mono", 11)).pack(anchor=tk.W)

    def _update_mozjpeg_status(self, *args):
        """Update MozJPEG status label"""
        if hasattr(self, 'mozjpeg_status'):
            if self.use_mozjpeg.get():
                self.mozjpeg_status.config(text="✅ Активний", foreground="green")
            else:
                self.mozjpeg_status.config(text="❌ Вимкнено (Pillow)", foreground="orange")

    def on_mode_change(self):
        """Handle mode change"""
        mode = self.mode.get()
        if mode == self.MODE_BALANCED:
            self.quality_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.quality_frame.pack_forget()

    def update_quality_label(self, val):
        self.quality_label.config(text=f"{int(float(val))}%")

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Виберіть JPG файли",
            filetypes=[("JPG файли", "*.jpg *.jpeg *.JPG *.JPEG"), ("Всі файли", "*.*")]
        )
        if files:
            self.add_paths(list(files))

    def select_folder(self):
        folder = filedialog.askdirectory(title="Виберіть папку з JPG файлами")
        if folder:
            self.add_paths([folder])

    def add_paths(self, paths: List[str]):
        for path in paths:
            if path not in self.selected_paths:
                self.selected_paths.append(path)
        self.update_file_list()

    def remove_selected(self):
        selection = self.file_listbox.curselection()
        for idx in reversed(selection):
            del self.selected_paths[idx]
        self.update_file_list()

    def clear_selection(self):
        self.selected_paths.clear()
        self.processed_files.clear()
        self.update_file_list()
        self.reset_results()

    def update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for path in self.selected_paths:
            name = os.path.basename(path)
            if os.path.isdir(path):
                name = f"📂 {name}/"
            else:
                name = f"📄 {name}"
            self.file_listbox.insert(tk.END, name)
        self.file_count_label.config(text=f"Файлів: {len(self.selected_paths)}")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Виберіть папку для збереження")
        if folder:
            self.output_folder = folder
            self.output_label.config(text=folder, foreground="black")

    def reset_output_folder(self):
        self.output_folder = None
        self.output_label.config(text="(та сама папка, що й оригінал)", foreground="gray")

    def reset_results(self):
        self.total_original = 0
        self.total_saved = 0
        self.processed_count = 0
        self.file_counter = 0
        self.original_label.config(text="—")
        self.new_label.config(text="—")
        self.saved_label.config(text="—")
        self.percent_label.config(text="—")
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Готовий до оптимізації")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def log(self, message: str, is_error: bool = False):
        self.log_text.config(state=tk.NORMAL)
        prefix = "❌" if is_error else "✅"
        self.log_text.insert(tk.END, f"{prefix} {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def format_size(self, bytes_size: int) -> str:
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} ТБ"

    def find_jpg_files(self) -> List[str]:
        """Find all JPG files in selected paths"""
        jpg_files = []
        for path in self.selected_paths:
            if os.path.isfile(path):
                if path.lower().endswith(('.jpg', '.jpeg')):
                    jpg_files.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg')):
                            jpg_files.append(os.path.join(root, file))
        return jpg_files

    def generate_output_path(self, original_path: str) -> str:
        """Generate output path based on settings"""
        original_dir = os.path.dirname(original_path)
        original_name = os.path.splitext(os.path.basename(original_path))[0]
        ext = os.path.splitext(original_path)[1]

        # Determine output directory
        if self.output_folder:
            if self.preserve_subfolders.get():
                # Find relative path from first selected folder
                for selected in self.selected_paths:
                    if os.path.isdir(selected) and original_path.startswith(selected):
                        rel_path = os.path.relpath(original_dir, selected)
                        output_dir = os.path.join(self.output_folder, rel_path)
                        break
                else:
                    output_dir = self.output_folder
            else:
                output_dir = self.output_folder
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = original_dir

        # Generate filename from template
        if self.overwrite_original.get():
            return original_path

        template = self.naming_template.get()
        with self._counter_lock:
            self.file_counter += 1
            counter_val = self.file_counter

        new_name = template.format(
            name=original_name,
            date=datetime.now().strftime("%Y%m%d_%H%M%S"),
            counter=str(counter_val).zfill(4)
        )

        output_path = os.path.join(output_dir, new_name + ext)

        # Handle conflicts
        counter = 1
        base_output = output_path
        while os.path.exists(output_path) and output_path != original_path:
            name_part = os.path.splitext(base_output)[0]
            output_path = f"{name_part}_{counter}{ext}"
            counter += 1

        return output_path

    def optimize_lossless(self, input_path: str, output_path: str) -> Tuple[int, int]:
        """Lossless optimization using MozJPEG jpegtran or Pillow"""
        original_size = os.path.getsize(input_path)

        if self.has_jpegtran and self.jpegtran_path:
            # Use MozJPEG jpegtran for true lossless optimization
            temp_path = output_path + '.tmp'

            # Always extract ICC profile first (jpegtran -copy none would strip it)
            icc_profile = self._extract_icc_profile(input_path)

            try:
                cmd = [self.jpegtran_path, "-optimize", "-progressive", "-copy", "all", "-outfile", temp_path, input_path]
                if self.remove_metadata.get():
                    cmd[4] = "none"
                subprocess.run(cmd, check=True, capture_output=True, timeout=60)

                # Restore ICC profile if it was stripped by -copy none
                if self.remove_metadata.get() and icc_profile:
                    self._inject_icc_profile(temp_path, icc_profile)

                new_size = os.path.getsize(temp_path)
                if new_size < original_size:
                    shutil.move(temp_path, output_path)
                    return (original_size, original_size - new_size)
                else:
                    os.remove(temp_path)
                    if output_path != input_path:
                        shutil.copy2(input_path, output_path)
                    return (original_size, 0)
            except Exception as e:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise e
        else:
            # Fallback to Pillow with quality 100
            img = Image.open(input_path)

            exif_data = None
            if not self.remove_metadata.get():
                try:
                    exif_data = img.info.get('exif')
                except:
                    pass

            # ICC profile is ALWAYS preserved — it's color rendering info, not personal metadata
            icc_profile = None
            try:
                icc_profile = img.info.get('icc_profile')
            except:
                pass

            if img.mode in ('RGBA', 'P', 'CMYK'):
                img = img.convert('RGB')

            save_kwargs = {'quality': 100, 'optimize': True, 'progressive': True}
            if exif_data:
                save_kwargs['exif'] = exif_data
            if icc_profile:
                save_kwargs['icc_profile'] = icc_profile

            temp_path = output_path + '.tmp'
            img.save(temp_path, 'JPEG', **save_kwargs)
            img.close()

            new_size = os.path.getsize(temp_path)
            if new_size < original_size:
                shutil.move(temp_path, output_path)
                return (original_size, original_size - new_size)
            else:
                os.remove(temp_path)
                if output_path != input_path:
                    shutil.copy2(input_path, output_path)
                return (original_size, 0)

    def optimize_balanced(self, input_path: str, output_path: str, quality: int) -> Tuple[int, int]:
        """Balanced optimization with quality setting - uses MozJPEG if available and enabled"""
        original_size = os.path.getsize(input_path)

        if self.has_mozjpeg and self.use_mozjpeg.get():
            # Use MozJPEG for better compression
            return self._optimize_with_mozjpeg(input_path, output_path, quality, original_size)
        else:
            # Fallback to Pillow
            return self._optimize_with_pillow(input_path, output_path, quality, original_size)

    def _extract_icc_profile(self, filepath: str) -> Optional[bytes]:
        """Extract ICC color profile from a JPEG file"""
        try:
            img = Image.open(filepath)
            icc = img.info.get('icc_profile')
            img.close()
            return icc
        except:
            return None

    def _inject_icc_profile(self, filepath: str, icc_data: bytes):
        """Inject ICC color profile into a JPEG file without re-encoding.
        This preserves exact pixel data while adding the color profile metadata."""
        if not icc_data:
            return

        with open(filepath, 'rb') as f:
            jpeg_data = f.read()

        # Verify JPEG signature
        if jpeg_data[:2] != b'\xff\xd8':
            return

        # Build ICC APP2 marker segment
        # Format: 0xFFE2 + length(2 bytes) + "ICC_PROFILE\0" + chunk_num(1) + total_chunks(1) + profile_data
        max_chunk_data = 65533 - 14  # Max data per chunk (65519 bytes)

        if len(icc_data) <= max_chunk_data:
            # Single chunk (covers virtually all real-world ICC profiles)
            icc_header = b'ICC_PROFILE\x00\x01\x01'
            marker_data = icc_header + icc_data
            marker_length = len(marker_data) + 2
            app2_segment = b'\xff\xe2' + marker_length.to_bytes(2, 'big') + marker_data
        else:
            # Multiple chunks for very large profiles
            chunks = []
            total_chunks = (len(icc_data) + max_chunk_data - 1) // max_chunk_data
            for i in range(total_chunks):
                chunk_data = icc_data[i * max_chunk_data:(i + 1) * max_chunk_data]
                icc_header = b'ICC_PROFILE\x00' + bytes([i + 1, total_chunks])
                marker_data = icc_header + chunk_data
                marker_length = len(marker_data) + 2
                chunks.append(b'\xff\xe2' + marker_length.to_bytes(2, 'big') + marker_data)
            app2_segment = b''.join(chunks)

        # Insert after SOI marker (first 2 bytes)
        new_jpeg = jpeg_data[:2] + app2_segment + jpeg_data[2:]

        with open(filepath, 'wb') as f:
            f.write(new_jpeg)

    def _optimize_with_mozjpeg(self, input_path: str, output_path: str, quality: int, original_size: int) -> Tuple[int, int]:
        """Optimize using MozJPEG cjpeg (better quality at same file size)"""
        temp_ppm = output_path + '.ppm'
        temp_jpg = output_path + '.tmp'

        # Extract ICC profile BEFORE decoding (djpeg strips it)
        # ICC profile is ALWAYS preserved — it's color rendering info, not personal metadata
        icc_profile = self._extract_icc_profile(input_path)

        try:
            # Decode JPEG to PPM using djpeg
            djpeg_path = self.mozjpeg_path.replace('cjpeg', 'djpeg')
            subprocess.run([djpeg_path, "-outfile", temp_ppm, input_path],
                          check=True, capture_output=True, timeout=120)

            # Encode PPM to JPEG using MozJPEG cjpeg
            cmd = [self.mozjpeg_path]

            # Add quality
            cmd.extend(["-quality", str(quality)])

            # Add subsampling based on quality (must be before input file)
            if quality >= 90:
                cmd.extend(["-sample", "1x1"])  # 4:4:4 for high quality

            # Add other options
            cmd.extend(["-progressive", "-optimize"])

            # Add output file and input file (must be last)
            cmd.extend(["-outfile", temp_jpg, temp_ppm])

            subprocess.run(cmd, check=True, capture_output=True, timeout=120)

            # Copy EXIF from original if needed
            if not self.remove_metadata.get():
                try:
                    # Read EXIF from original
                    original_exif = piexif.load(input_path)
                    if original_exif:
                        piexif.insert(piexif.dump(original_exif), temp_jpg)
                except:
                    pass

            # Restore ICC color profile (critical for color accuracy!)
            if icc_profile:
                self._inject_icc_profile(temp_jpg, icc_profile)

            new_size = os.path.getsize(temp_jpg)

            # Only use if smaller
            if new_size < original_size:
                shutil.move(temp_jpg, output_path)
                return (original_size, original_size - new_size)
            else:
                os.remove(temp_jpg)
                if output_path != input_path:
                    shutil.copy2(input_path, output_path)
                return (original_size, 0)

        finally:
            # Cleanup temp files
            if os.path.exists(temp_ppm):
                os.remove(temp_ppm)
            if os.path.exists(temp_jpg):
                try:
                    os.remove(temp_jpg)
                except:
                    pass

    def _optimize_with_pillow(self, input_path: str, output_path: str, quality: int, original_size: int) -> Tuple[int, int]:
        """Fallback optimization using Pillow"""
        img = Image.open(input_path)

        exif_data = None
        if not self.remove_metadata.get():
            try:
                exif_data = img.info.get('exif')
            except:
                pass

        # ICC profile is ALWAYS preserved — it's color rendering info, not personal metadata
        icc_profile = None
        try:
            icc_profile = img.info.get('icc_profile')
        except:
            pass

        if img.mode in ('RGBA', 'P', 'CMYK'):
            img = img.convert('RGB')

        # Apply slight sharpening to compensate for compression
        if quality < 90:
            img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=20, threshold=2))

        save_kwargs = {
            'quality': quality,
            'optimize': True,
            'progressive': True,
            'subsampling': 0 if quality >= 90 else 2  # 4:4:4 for high quality, 4:2:0 otherwise
        }
        if exif_data:
            save_kwargs['exif'] = exif_data
        if icc_profile:
            save_kwargs['icc_profile'] = icc_profile

        temp_path = output_path + '.tmp'
        img.save(temp_path, 'JPEG', **save_kwargs)
        img.close()

        new_size = os.path.getsize(temp_path)

        if new_size < original_size:
            shutil.move(temp_path, output_path)
            return (original_size, original_size - new_size)
        else:
            os.remove(temp_path)
            if output_path != input_path:
                shutil.copy2(input_path, output_path)
            return (original_size, 0)

    def optimize_maximum(self, input_path: str, output_path: str) -> Tuple[int, int]:
        """Maximum compression using MozJPEG"""
        original_size = os.path.getsize(input_path)

        if self.has_mozjpeg and self.use_mozjpeg.get():
            return self._optimize_with_mozjpeg(input_path, output_path, 70, original_size)
        else:
            img = Image.open(input_path)

            # ICC profile is ALWAYS preserved — it's color rendering info, not personal metadata
            icc_profile = None
            try:
                icc_profile = img.info.get('icc_profile')
            except:
                pass

            if img.mode in ('RGBA', 'P', 'CMYK'):
                img = img.convert('RGB')

            save_kwargs = {
                'quality': 70,
                'optimize': True,
                'progressive': True,
                'subsampling': 2  # 4:2:0 for maximum compression
            }
            if icc_profile:
                save_kwargs['icc_profile'] = icc_profile

            temp_path = output_path + '.tmp'
            img.save(temp_path, 'JPEG', **save_kwargs)
            img.close()

            new_size = os.path.getsize(temp_path)
            shutil.move(temp_path, output_path)

            return (original_size, original_size - new_size)

    def optimize_file(self, filepath: str) -> Optional[Tuple[int, int, str, str]]:
        """Optimize single file based on current mode"""
        try:
            output_path = self.generate_output_path(filepath)
            mode = self.mode.get()

            if mode == self.MODE_LOSSLESS:
                original, saved = self.optimize_lossless(filepath, output_path)
            elif mode == self.MODE_BALANCED:
                original, saved = self.optimize_balanced(filepath, output_path, self.quality.get())
            else:  # MODE_MAXIMUM
                original, saved = self.optimize_maximum(filepath, output_path)

            return (original, saved, filepath, output_path)

        except Exception as e:
            return (0, 0, filepath, "", str(e))

    def start_optimization(self):
        if not self.selected_paths:
            messagebox.showwarning("Увага", "Спочатку виберіть файли або папку!")
            return

        if self.is_processing:
            return

        self.is_processing = True
        self.optimize_btn.config(state=tk.DISABLED)
        self.reset_results()
        self.processed_files.clear()

        thread = threading.Thread(target=self.run_optimization)
        thread.daemon = True
        thread.start()

    def run_optimization(self):
        jpg_files = self.find_jpg_files()

        if not jpg_files:
            self.root.after(0, lambda: self.log("Не знайдено жодного JPG файлу!", is_error=True))
            self.root.after(0, self.finish_optimization)
            return

        self.total_count = len(jpg_files)
        mode_name = {"lossless": "Lossless", "balanced": "Balanced", "maximum": "Maximum"}[self.mode.get()]

        self.root.after(0, lambda: self.log(f"Знайдено {self.total_count} файлів. Режим: {mode_name}"))

        max_workers = min(os.cpu_count() or 4, 8)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.optimize_file, f): f for f in jpg_files}

            for future in as_completed(futures):
                result = future.result()
                self.processed_count += 1

                if result:
                    if len(result) == 5:  # Error
                        _, _, filepath, _, error = result
                        self.root.after(0, lambda f=filepath, e=error: self.log(f"{os.path.basename(f)}: {e}", is_error=True))
                    else:
                        original, saved, input_path, output_path = result
                        self.total_original += original
                        self.total_saved += saved
                        self.processed_files.append((input_path, output_path))

                        if saved > 0:
                            self.root.after(0, lambda f=input_path, s=saved:
                                self.log(f"{os.path.basename(f)}: -{self.format_size(s)}"))
                        else:
                            self.root.after(0, lambda f=input_path:
                                self.log(f"{os.path.basename(f)}: вже оптимізовано"))

                progress = (self.processed_count / self.total_count) * 100
                self.root.after(0, lambda p=progress: self.update_progress(p))

        self.root.after(0, self.finish_optimization)

    def update_progress(self, progress: float):
        self.progress_bar['value'] = progress
        self.progress_label.config(text=f"Оброблено: {self.processed_count} / {self.total_count} ({progress:.1f}%)")

        self.original_label.config(text=self.format_size(self.total_original))
        new_size = self.total_original - self.total_saved
        self.new_label.config(text=self.format_size(new_size))
        self.saved_label.config(text=self.format_size(self.total_saved))

        if self.total_original > 0:
            percent = (self.total_saved / self.total_original) * 100
            self.percent_label.config(text=f"{percent:.1f}%")

    def finish_optimization(self):
        self.is_processing = False
        self.optimize_btn.config(state=tk.NORMAL)
        self.progress_label.config(text="Завершено!")

        if self.total_saved > 0:
            self.log(f"\n🎉 Готово! Зекономлено {self.format_size(self.total_saved)}")
        else:
            self.log("\nВсі файли вже оптимізовано")

    def show_comparison(self):
        """Show comparison window for last processed file"""
        if not self.processed_files:
            messagebox.showinfo("Інформація", "Спочатку оптимізуйте файли для порівняння")
            return

        # Let user select file to compare
        if len(self.processed_files) == 1:
            original, optimized = self.processed_files[0]
            NavigatorCompareWindow(self.root, original, optimized)
        else:
            # Show selection dialog
            select_win = tk.Toplevel(self.root)
            select_win.title("Вибрати файл для порівняння")
            select_win.geometry("400x300")

            ttk.Label(select_win, text="Виберіть файл для порівняння:").pack(pady=10)

            listbox = tk.Listbox(select_win, font=("SF Pro Display", 11), bg='white', fg='black')
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            for orig, opt in self.processed_files:
                listbox.insert(tk.END, os.path.basename(orig))

            def on_select():
                sel = listbox.curselection()
                if sel:
                    original, optimized = self.processed_files[sel[0]]
                    select_win.destroy()
                    NavigatorCompareWindow(self.root, original, optimized)

            ttk.Button(select_win, text="Порівняти", command=on_select).pack(pady=10)

    def run(self):
        self.root.mainloop()


def main():
    app = JPGOptimizerPro()
    app.run()


if __name__ == "__main__":
    main()
