"""
JPG Optimizer Pro - Web Version (Streamlit)
Оптимізація JPG зображень через браузер
"""

import streamlit as st
import os
import io
import zipfile
import tempfile
import subprocess
from PIL import Image, ImageFilter
from datetime import datetime
from typing import Tuple, Optional, List
import piexif

# Page config
st.set_page_config(
    page_title="JPG Optimizer Pro",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0;
    }
    .sub-header {
        color: #666;
        margin-top: 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .stat-label {
        opacity: 0.9;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stImage > img {
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def check_mozjpeg() -> Tuple[bool, Optional[str]]:
    """Check if MozJPEG is available"""
    paths = ["/opt/homebrew/opt/mozjpeg/bin/cjpeg", "/usr/local/opt/mozjpeg/bin/cjpeg"]
    for path in paths:
        if os.path.exists(path):
            return True, path
    return False, None


def format_size(bytes_size: int) -> str:
    """Format bytes to human readable"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} ТБ"


def optimize_with_pillow(img: Image.Image, quality: int, remove_metadata: bool) -> Tuple[bytes, dict]:
    """Optimize image using Pillow"""
    # Convert if needed
    if img.mode in ('RGBA', 'P', 'CMYK'):
        img = img.convert('RGB')

    # Get EXIF
    exif_data = None
    if not remove_metadata:
        try:
            exif_data = img.info.get('exif')
        except:
            pass

    # Apply slight sharpening for compression compensation
    if quality < 90:
        img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=20, threshold=2))

    # Save to buffer
    buffer = io.BytesIO()
    save_kwargs = {
        'quality': quality,
        'optimize': True,
        'progressive': True,
        'subsampling': 0 if quality >= 90 else 2
    }
    if exif_data:
        save_kwargs['exif'] = exif_data

    img.save(buffer, 'JPEG', **save_kwargs)
    buffer.seek(0)

    return buffer.getvalue(), {'width': img.width, 'height': img.height}


def optimize_with_mozjpeg(img: Image.Image, quality: int, remove_metadata: bool, mozjpeg_path: str, original_bytes: bytes) -> Tuple[bytes, dict]:
    """Optimize using MozJPEG"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save original to temp file
        input_path = os.path.join(tmpdir, "input.jpg")
        ppm_path = os.path.join(tmpdir, "temp.ppm")
        output_path = os.path.join(tmpdir, "output.jpg")

        # Write original
        with open(input_path, 'wb') as f:
            f.write(original_bytes)

        # Decode to PPM
        djpeg_path = mozjpeg_path.replace('cjpeg', 'djpeg')
        subprocess.run([djpeg_path, "-outfile", ppm_path, input_path],
                      check=True, capture_output=True, timeout=60)

        # Encode with MozJPEG
        cmd = [mozjpeg_path, "-quality", str(quality)]
        if quality >= 90:
            cmd.extend(["-sample", "1x1"])
        cmd.extend(["-progressive", "-optimize", "-outfile", output_path, ppm_path])

        subprocess.run(cmd, check=True, capture_output=True, timeout=60)

        # Copy EXIF if needed
        if not remove_metadata:
            try:
                original_exif = piexif.load(input_path)
                if original_exif:
                    piexif.insert(piexif.dump(original_exif), output_path)
            except:
                pass

        # Read result
        with open(output_path, 'rb') as f:
            result = f.read()

        return result, {'width': img.width, 'height': img.height}


def optimize_lossless(original_bytes: bytes, remove_metadata: bool) -> bytes:
    """Lossless optimization using jpegtran"""
    jpegtran_paths = ["/opt/homebrew/opt/mozjpeg/bin/jpegtran", "/usr/local/opt/mozjpeg/bin/jpegtran"]
    jpegtran_path = None
    for path in jpegtran_paths:
        if os.path.exists(path):
            jpegtran_path = path
            break

    if not jpegtran_path:
        # Fallback - return original
        return original_bytes

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.jpg")
        output_path = os.path.join(tmpdir, "output.jpg")

        with open(input_path, 'wb') as f:
            f.write(original_bytes)

        copy_mode = "none" if remove_metadata else "all"
        cmd = [jpegtran_path, "-optimize", "-progressive", "-copy", copy_mode, "-outfile", output_path, input_path]

        subprocess.run(cmd, check=True, capture_output=True, timeout=60)

        with open(output_path, 'rb') as f:
            return f.read()


def main():
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<p class="main-header">🖼️ JPG Optimizer Pro</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Професійна оптимізація JPG зображень</p>', unsafe_allow_html=True)

    # Check MozJPEG
    has_mozjpeg, mozjpeg_path = check_mozjpeg()

    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Налаштування")

        # Mode selection
        mode = st.radio(
            "Режим оптимізації",
            ["🔒 Lossless", "⚖️ Balanced", "📦 Maximum"],
            index=1,
            help="Lossless - без втрат, Balanced - баланс, Maximum - максимальне стиснення"
        )

        # Quality slider (for Balanced mode)
        quality = 85
        if "Balanced" in mode:
            quality = st.slider("Якість", 60, 100, 85, help="Вища якість = більший файл")

        # Options
        st.divider()
        remove_metadata = st.checkbox("Видалити EXIF метадані", help="Зменшує розмір, але втрачає дату/GPS")

        use_mozjpeg = False
        if has_mozjpeg:
            use_mozjpeg = st.checkbox("Використовувати MozJPEG", value=True, help="Краще стиснення")
            if use_mozjpeg:
                st.success("✅ MozJPEG активний")

        # Info
        st.divider()
        st.caption("📊 Рекомендації:")
        st.caption("• Архів фото: Lossless або 90-95%")
        st.caption("• Загальне: 80-85%")
        st.caption("• Веб: Maximum (70%)")

    # Main content
    uploaded_files = st.file_uploader(
        "📂 Завантажте JPG файли",
        type=['jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Перетягніть файли сюди або натисніть для вибору"
    )

    if uploaded_files:
        st.info(f"📁 Завантажено файлів: {len(uploaded_files)}")

        if st.button("🚀 Оптимізувати", type="primary", use_container_width=True):
            # Initialize session state for results
            results = []
            total_original = 0
            total_optimized = 0

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Обробка: {uploaded_file.name}...")

                try:
                    # Read original
                    original_bytes = uploaded_file.read()
                    original_size = len(original_bytes)
                    total_original += original_size

                    # Open image
                    img = Image.open(io.BytesIO(original_bytes))

                    # Optimize based on mode
                    if "Lossless" in mode:
                        optimized_bytes = optimize_lossless(original_bytes, remove_metadata)
                    elif "Maximum" in mode:
                        if use_mozjpeg and has_mozjpeg:
                            optimized_bytes, _ = optimize_with_mozjpeg(img, 70, remove_metadata, mozjpeg_path, original_bytes)
                        else:
                            optimized_bytes, _ = optimize_with_pillow(img, 70, remove_metadata)
                    else:  # Balanced
                        if use_mozjpeg and has_mozjpeg:
                            optimized_bytes, _ = optimize_with_mozjpeg(img, quality, remove_metadata, mozjpeg_path, original_bytes)
                        else:
                            optimized_bytes, _ = optimize_with_pillow(img, quality, remove_metadata)

                    optimized_size = len(optimized_bytes)

                    # Only use if smaller
                    if optimized_size >= original_size:
                        optimized_bytes = original_bytes
                        optimized_size = original_size

                    total_optimized += optimized_size

                    results.append({
                        'name': uploaded_file.name,
                        'original_size': original_size,
                        'optimized_size': optimized_size,
                        'saved': original_size - optimized_size,
                        'original_bytes': original_bytes,
                        'optimized_bytes': optimized_bytes,
                        'image': img
                    })

                except Exception as e:
                    st.error(f"❌ Помилка обробки {uploaded_file.name}: {str(e)}")

                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.text("✅ Готово!")

            # Store results in session state
            st.session_state['results'] = results
            st.session_state['total_original'] = total_original
            st.session_state['total_optimized'] = total_optimized

    # Display results
    if 'results' in st.session_state and st.session_state['results']:
        results = st.session_state['results']
        total_original = st.session_state['total_original']
        total_optimized = st.session_state['total_optimized']
        total_saved = total_original - total_optimized
        saved_percent = (total_saved / total_original * 100) if total_original > 0 else 0

        st.divider()

        # Stats cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📄 Оригінал", format_size(total_original))
        with col2:
            st.metric("📦 Після", format_size(total_optimized))
        with col3:
            st.metric("💾 Зекономлено", format_size(total_saved), f"{saved_percent:.1f}%")
        with col4:
            st.metric("📊 Файлів", len(results))

        st.divider()

        # Download section
        st.subheader("📥 Завантажити результати")

        col1, col2 = st.columns(2)

        with col1:
            # Download all as ZIP
            if len(results) > 1:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for r in results:
                        # Add _optimized suffix
                        name, ext = os.path.splitext(r['name'])
                        new_name = f"{name}_optimized{ext}"
                        zf.writestr(new_name, r['optimized_bytes'])

                zip_buffer.seek(0)
                st.download_button(
                    "📦 Завантажити всі (ZIP)",
                    zip_buffer,
                    file_name=f"optimized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        with col2:
            # Download individual
            if len(results) == 1:
                r = results[0]
                name, ext = os.path.splitext(r['name'])
                st.download_button(
                    f"💾 Завантажити {r['name']}",
                    r['optimized_bytes'],
                    file_name=f"{name}_optimized{ext}",
                    mime="image/jpeg",
                    use_container_width=True
                )

        st.divider()

        # Comparison view
        st.subheader("🔍 Порівняння До / Після")

        if len(results) > 1:
            selected_file = st.selectbox(
                "Виберіть файл для порівняння",
                options=[r['name'] for r in results]
            )
            selected = next(r for r in results if r['name'] == selected_file)
        else:
            selected = results[0]

        # File info
        saved_pct = (selected['saved'] / selected['original_size'] * 100) if selected['original_size'] > 0 else 0
        st.info(f"📊 {selected['name']}: {format_size(selected['original_size'])} → {format_size(selected['optimized_size'])} (зекономлено {format_size(selected['saved'])}, {saved_pct:.1f}%)")

        # Side by side comparison
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Оригінал**")
            original_img = Image.open(io.BytesIO(selected['original_bytes']))
            st.image(original_img, use_container_width=True)

        with col2:
            st.markdown("**Оптимізовано**")
            optimized_img = Image.open(io.BytesIO(selected['optimized_bytes']))
            st.image(optimized_img, use_container_width=True)

        # Zoom comparison
        st.subheader("🔬 Детальне порівняння")
        st.caption("Перетягніть слайдер для вибору області")

        zoom_level = st.slider("Збільшення", 2, 8, 4)

        # Position selectors
        col1, col2 = st.columns(2)
        with col1:
            x_pos = st.slider("Позиція X", 0, 100, 50, help="Горизонтальна позиція")
        with col2:
            y_pos = st.slider("Позиція Y", 0, 100, 50, help="Вертикальна позиція")

        # Calculate crop region
        img_w, img_h = original_img.size
        crop_size = min(img_w, img_h) // zoom_level

        center_x = int(x_pos / 100 * img_w)
        center_y = int(y_pos / 100 * img_h)

        left = max(0, center_x - crop_size // 2)
        top = max(0, center_y - crop_size // 2)
        right = min(img_w, left + crop_size)
        bottom = min(img_h, top + crop_size)

        # Crop and display
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Оригінал (збільшено)**")
            cropped_original = original_img.crop((left, top, right, bottom))
            st.image(cropped_original.resize((400, 400), Image.Resampling.NEAREST), use_container_width=True)

        with col2:
            st.markdown("**Оптимізовано (збільшено)**")
            cropped_optimized = optimized_img.crop((left, top, right, bottom))
            st.image(cropped_optimized.resize((400, 400), Image.Resampling.NEAREST), use_container_width=True)

        # Results table
        st.divider()
        st.subheader("📋 Деталі обробки")

        table_data = []
        for r in results:
            saved_pct = (r['saved'] / r['original_size'] * 100) if r['original_size'] > 0 else 0
            table_data.append({
                "Файл": r['name'],
                "Оригінал": format_size(r['original_size']),
                "Після": format_size(r['optimized_size']),
                "Зекономлено": format_size(r['saved']),
                "%": f"{saved_pct:.1f}%"
            })

        st.dataframe(table_data, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
