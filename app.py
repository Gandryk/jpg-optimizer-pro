"""
JPG Optimizer Pro - Web Version (Streamlit)
Професійний оптимізатор JPG з темною темою та мобільною адаптацією
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
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Dark theme with neon accents CSS
st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Root variables */
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-card: #1a1a24;
        --bg-hover: #22222e;
        --text-primary: #ffffff;
        --text-secondary: #a0a0b0;
        --neon-cyan: #00f5ff;
        --neon-purple: #bf00ff;
        --neon-pink: #ff00aa;
        --neon-green: #00ff88;
        --gradient-1: linear-gradient(135deg, #00f5ff 0%, #bf00ff 100%);
        --gradient-2: linear-gradient(135deg, #ff00aa 0%, #bf00ff 100%);
        --shadow-neon: 0 0 20px rgba(0, 245, 255, 0.3);
    }

    /* Global styles */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main container */
    .main .block-container {
        padding: 1rem 1rem 3rem 1rem;
        max-width: 1200px;
    }

    /* Header styles */
    .main-header {
        text-align: center;
        padding: 2rem 1rem;
        margin-bottom: 1rem;
    }

    .app-title {
        font-size: clamp(2rem, 5vw, 3.5rem);
        font-weight: 700;
        background: var(--gradient-1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
    }

    .app-subtitle {
        color: var(--text-secondary);
        font-size: clamp(0.9rem, 2vw, 1.1rem);
    }

    /* Card styles */
    .card {
        background: var(--bg-card);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }

    .card:hover {
        border-color: rgba(0, 245, 255, 0.2);
        box-shadow: var(--shadow-neon);
    }

    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Upload area */
    .upload-area {
        border: 2px dashed rgba(0, 245, 255, 0.3);
        border-radius: 16px;
        padding: 3rem 2rem;
        text-align: center;
        background: rgba(0, 245, 255, 0.02);
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .upload-area:hover {
        border-color: var(--neon-cyan);
        background: rgba(0, 245, 255, 0.05);
        box-shadow: var(--shadow-neon);
    }

    .upload-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    .upload-text {
        color: var(--text-primary);
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }

    .upload-hint {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    /* Mode buttons */
    .mode-btn {
        background: var(--bg-card);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-bottom: 0.5rem;
    }

    .mode-btn:hover {
        border-color: var(--neon-cyan);
        transform: translateY(-2px);
    }

    .mode-btn.active {
        border-color: var(--neon-cyan);
        background: rgba(0, 245, 255, 0.1);
        box-shadow: var(--shadow-neon);
    }

    .mode-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .mode-name {
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.25rem;
    }

    .mode-desc {
        font-size: 0.75rem;
        color: var(--text-secondary);
    }

    /* Stats cards */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .stat-card {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
    }

    .stat-value {
        font-size: clamp(1.5rem, 4vw, 2rem);
        font-weight: 700;
        background: var(--gradient-1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .stat-label {
        color: var(--text-secondary);
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }

    /* Progress bar */
    .progress-container {
        background: var(--bg-secondary);
        border-radius: 10px;
        height: 8px;
        overflow: hidden;
        margin: 1rem 0;
    }

    .progress-bar {
        height: 100%;
        background: var(--gradient-1);
        border-radius: 10px;
        transition: width 0.3s ease;
        box-shadow: 0 0 10px rgba(0, 245, 255, 0.5);
    }

    /* Buttons */
    .stButton > button {
        background: var(--gradient-1) !important;
        color: #000 !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-neon) !important;
    }

    .stDownloadButton > button {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--neon-cyan) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }

    .stDownloadButton > button:hover {
        background: rgba(0, 245, 255, 0.1) !important;
        box-shadow: var(--shadow-neon) !important;
    }

    /* Sliders */
    .stSlider > div > div {
        background: var(--bg-secondary) !important;
    }

    .stSlider > div > div > div > div {
        background: var(--gradient-1) !important;
    }

    /* Checkboxes */
    .stCheckbox > label {
        color: var(--text-primary) !important;
    }

    /* Radio buttons */
    .stRadio > label {
        color: var(--text-primary) !important;
    }

    .stRadio > div {
        background: var(--bg-card);
        border-radius: 12px;
        padding: 0.5rem;
    }

    /* File uploader */
    .stFileUploader > div {
        background: var(--bg-card) !important;
        border: 2px dashed rgba(0, 245, 255, 0.3) !important;
        border-radius: 16px !important;
    }

    .stFileUploader > div:hover {
        border-color: var(--neon-cyan) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }

    /* Comparison section */
    .comparison-container {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .comparison-image {
        flex: 1;
        min-width: 280px;
        background: var(--bg-card);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(255,255,255,0.05);
    }

    .comparison-label {
        text-align: center;
        font-weight: 600;
        margin-bottom: 0.5rem;
        padding: 0.5rem;
        border-radius: 8px;
    }

    .label-before {
        background: rgba(255, 0, 170, 0.2);
        color: var(--neon-pink);
    }

    .label-after {
        background: rgba(0, 255, 136, 0.2);
        color: var(--neon-green);
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem 0.5rem 2rem 0.5rem;
        }

        .main-header {
            padding: 1rem 0.5rem;
        }

        .card {
            padding: 1rem;
            border-radius: 12px;
        }

        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }

        .stat-card {
            padding: 1rem;
        }

        .upload-area {
            padding: 2rem 1rem;
        }

        .comparison-image {
            min-width: 100%;
        }
    }

    /* Animations */
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 245, 255, 0.3); }
        50% { box-shadow: 0 0 30px rgba(0, 245, 255, 0.5); }
    }

    .glow-animation {
        animation: glow 2s ease-in-out infinite;
    }

    /* Success message */
    .success-message {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid var(--neon-green);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        color: var(--neon-green);
        margin: 1rem 0;
    }

    /* Table styles */
    .stDataFrame {
        background: var(--bg-card) !important;
        border-radius: 12px !important;
    }

    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.1) !important;
        margin: 2rem 0 !important;
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


def extract_icc_profile(img: Image.Image) -> Optional[bytes]:
    """Extract ICC color profile from a PIL Image"""
    try:
        return img.info.get('icc_profile')
    except:
        return None


def inject_icc_profile(jpeg_data: bytes, icc_data: bytes) -> bytes:
    """Inject ICC color profile into JPEG bytes without re-encoding.
    Preserves exact pixel data while adding the color profile metadata."""
    if not icc_data:
        return jpeg_data

    # Verify JPEG signature
    if jpeg_data[:2] != b'\xff\xd8':
        return jpeg_data

    # Build ICC APP2 marker segment
    # Format: 0xFFE2 + length(2 bytes) + "ICC_PROFILE\0" + chunk_num(1) + total_chunks(1) + data
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
    return jpeg_data[:2] + app2_segment + jpeg_data[2:]


def optimize_with_pillow(img: Image.Image, quality: int, remove_metadata: bool) -> Tuple[bytes, dict]:
    """Optimize image using Pillow"""
    # ICC profile is ALWAYS preserved — it's color rendering info, not personal metadata
    icc_profile = extract_icc_profile(img)

    if img.mode in ('RGBA', 'P', 'CMYK'):
        img = img.convert('RGB')

    exif_data = None
    if not remove_metadata:
        try:
            exif_data = img.info.get('exif')
        except:
            pass

    if quality < 90:
        img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=20, threshold=2))

    buffer = io.BytesIO()
    save_kwargs = {
        'quality': quality,
        'optimize': True,
        'progressive': True,
        'subsampling': 0 if quality >= 90 else 2
    }
    if exif_data:
        save_kwargs['exif'] = exif_data
    if icc_profile:
        save_kwargs['icc_profile'] = icc_profile

    img.save(buffer, 'JPEG', **save_kwargs)
    buffer.seek(0)

    return buffer.getvalue(), {'width': img.width, 'height': img.height}


def optimize_with_mozjpeg(img: Image.Image, quality: int, remove_metadata: bool, mozjpeg_path: str, original_bytes: bytes) -> Tuple[bytes, dict]:
    """Optimize using MozJPEG"""
    # Extract ICC profile BEFORE decoding (djpeg strips it)
    # ICC profile is ALWAYS preserved — it's color rendering info, not personal metadata
    icc_profile = extract_icc_profile(img)

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.jpg")
        ppm_path = os.path.join(tmpdir, "temp.ppm")
        output_path = os.path.join(tmpdir, "output.jpg")

        with open(input_path, 'wb') as f:
            f.write(original_bytes)

        djpeg_path = mozjpeg_path.replace('cjpeg', 'djpeg')
        subprocess.run([djpeg_path, "-outfile", ppm_path, input_path],
                      check=True, capture_output=True, timeout=60)

        cmd = [mozjpeg_path, "-quality", str(quality)]
        if quality >= 90:
            cmd.extend(["-sample", "1x1"])
        cmd.extend(["-progressive", "-optimize", "-outfile", output_path, ppm_path])

        subprocess.run(cmd, check=True, capture_output=True, timeout=60)

        if not remove_metadata:
            try:
                original_exif = piexif.load(input_path)
                if original_exif:
                    piexif.insert(piexif.dump(original_exif), output_path)
            except:
                pass

        with open(output_path, 'rb') as f:
            result_bytes = f.read()

        # Restore ICC color profile (critical for color accuracy!)
        if icc_profile:
            result_bytes = inject_icc_profile(result_bytes, icc_profile)

        return result_bytes, {'width': img.width, 'height': img.height}


def optimize_lossless(original_bytes: bytes, remove_metadata: bool) -> bytes:
    """Lossless optimization using jpegtran"""
    jpegtran_paths = ["/opt/homebrew/opt/mozjpeg/bin/jpegtran", "/usr/local/opt/mozjpeg/bin/jpegtran"]
    jpegtran_path = None
    for path in jpegtran_paths:
        if os.path.exists(path):
            jpegtran_path = path
            break

    if not jpegtran_path:
        return original_bytes

    # Always extract ICC profile first (jpegtran -copy none would strip it)
    icc_profile = None
    try:
        img = Image.open(io.BytesIO(original_bytes))
        icc_profile = extract_icc_profile(img)
        img.close()
    except:
        pass

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.jpg")
        output_path = os.path.join(tmpdir, "output.jpg")

        with open(input_path, 'wb') as f:
            f.write(original_bytes)

        copy_mode = "none" if remove_metadata else "all"
        cmd = [jpegtran_path, "-optimize", "-progressive", "-copy", copy_mode, "-outfile", output_path, input_path]

        subprocess.run(cmd, check=True, capture_output=True, timeout=60)

        with open(output_path, 'rb') as f:
            result_bytes = f.read()

        # Restore ICC profile if it was stripped by -copy none
        if remove_metadata and icc_profile:
            result_bytes = inject_icc_profile(result_bytes, icc_profile)

        return result_bytes


def main():
    # Check MozJPEG
    has_mozjpeg, mozjpeg_path = check_mozjpeg()

    # Header
    st.markdown("""
    <div class="main-header">
        <div class="app-title">🖼️ JPG Optimizer Pro</div>
        <div class="app-subtitle">Професійна оптимізація зображень • Швидко • Безпечно • Безкоштовно</div>
    </div>
    """, unsafe_allow_html=True)

    # Settings in expander (better for mobile)
    with st.expander("⚙️ Налаштування", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            mode = st.radio(
                "Режим оптимізації",
                ["⚖️ Balanced", "🔒 Lossless", "📦 Maximum"],
                index=0,
                help="Balanced - баланс якості, Lossless - без втрат, Maximum - макс. стиснення"
            )

        with col2:
            quality = 85
            if "Balanced" in mode:
                quality = st.slider("Якість", 60, 100, 85)

            remove_metadata = st.checkbox("Видалити EXIF", help="Зменшує розмір. ICC кольоровий профіль зберігається завжди.")

    # File uploader
    st.markdown("""
    <div class="card">
        <div class="card-title">📂 Завантаження файлів</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Перетягніть файли або натисніть для вибору",
        type=['jpg', 'jpeg'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; color: var(--neon-cyan);">
            ✅ Завантажено: <strong>{len(uploaded_files)}</strong> файлів
        </div>
        """, unsafe_allow_html=True)

        # Optimize button
        if st.button("🚀 Оптимізувати", use_container_width=True):
            results = []
            total_original = 0
            total_optimized = 0

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.markdown(f"""
                <div style="text-align: center; color: var(--text-secondary);">
                    Обробка: {uploaded_file.name}...
                </div>
                """, unsafe_allow_html=True)

                try:
                    original_bytes = uploaded_file.read()
                    original_size = len(original_bytes)
                    total_original += original_size

                    img = Image.open(io.BytesIO(original_bytes))

                    if "Lossless" in mode:
                        optimized_bytes = optimize_lossless(original_bytes, remove_metadata)
                    elif "Maximum" in mode:
                        if has_mozjpeg:
                            optimized_bytes, _ = optimize_with_mozjpeg(img, 70, remove_metadata, mozjpeg_path, original_bytes)
                        else:
                            optimized_bytes, _ = optimize_with_pillow(img, 70, remove_metadata)
                    else:
                        if has_mozjpeg:
                            optimized_bytes, _ = optimize_with_mozjpeg(img, quality, remove_metadata, mozjpeg_path, original_bytes)
                        else:
                            optimized_bytes, _ = optimize_with_pillow(img, quality, remove_metadata)

                    optimized_size = len(optimized_bytes)

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
                    })

                except Exception as e:
                    st.error(f"❌ Помилка: {uploaded_file.name}")

                progress_bar.progress((i + 1) / len(uploaded_files))

            status_text.empty()
            progress_bar.empty()

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

        # Success message
        st.markdown(f"""
        <div class="success-message">
            ✨ Оптимізація завершена! Зекономлено {format_size(total_saved)} ({saved_percent:.1f}%)
        </div>
        """, unsafe_allow_html=True)

        # Stats
        st.markdown(f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{format_size(total_original)}</div>
                <div class="stat-label">До</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{format_size(total_optimized)}</div>
                <div class="stat-label">Після</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{format_size(total_saved)}</div>
                <div class="stat-label">Зекономлено</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{saved_percent:.0f}%</div>
                <div class="stat-label">Стиснення</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Download section
        st.markdown("""
        <div class="card">
            <div class="card-title">📥 Завантажити результати</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if len(results) > 1:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for r in results:
                        name, ext = os.path.splitext(r['name'])
                        new_name = f"{name}_opt{ext}"
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
            if len(results) == 1:
                r = results[0]
                name, ext = os.path.splitext(r['name'])
                st.download_button(
                    f"💾 Завантажити файл",
                    r['optimized_bytes'],
                    file_name=f"{name}_opt{ext}",
                    mime="image/jpeg",
                    use_container_width=True
                )

        # Comparison
        st.markdown("---")
        st.markdown("""
        <div class="card">
            <div class="card-title">🔍 Порівняння До / Після</div>
        </div>
        """, unsafe_allow_html=True)

        if len(results) > 1:
            selected_file = st.selectbox(
                "Виберіть файл",
                options=[r['name'] for r in results],
                label_visibility="collapsed"
            )
            selected = next(r for r in results if r['name'] == selected_file)
        else:
            selected = results[0]

        # Side by side
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="comparison-label label-before">📷 Оригінал</div>', unsafe_allow_html=True)
            original_img = Image.open(io.BytesIO(selected['original_bytes']))
            st.image(original_img, use_container_width=True)
            st.caption(f"Розмір: {format_size(selected['original_size'])}")

        with col2:
            st.markdown('<div class="comparison-label label-after">✨ Оптимізовано</div>', unsafe_allow_html=True)
            optimized_img = Image.open(io.BytesIO(selected['optimized_bytes']))
            st.image(optimized_img, use_container_width=True)
            st.caption(f"Розмір: {format_size(selected['optimized_size'])}")

        # Zoom comparison
        with st.expander("🔬 Детальне порівняння (зум)"):
            zoom_level = st.slider("Збільшення", 2, 8, 4, key="zoom")

            col1, col2 = st.columns(2)
            with col1:
                x_pos = st.slider("X", 0, 100, 50, key="xpos")
            with col2:
                y_pos = st.slider("Y", 0, 100, 50, key="ypos")

            img_w, img_h = original_img.size
            crop_size = min(img_w, img_h) // zoom_level

            center_x = int(x_pos / 100 * img_w)
            center_y = int(y_pos / 100 * img_h)

            left = max(0, center_x - crop_size // 2)
            top = max(0, center_y - crop_size // 2)
            right = min(img_w, left + crop_size)
            bottom = min(img_h, top + crop_size)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="comparison-label label-before">Оригінал (зум)</div>', unsafe_allow_html=True)
                cropped_original = original_img.crop((left, top, right, bottom))
                st.image(cropped_original.resize((400, 400), Image.Resampling.NEAREST), use_container_width=True)

            with col2:
                st.markdown('<div class="comparison-label label-after">Оптимізовано (зум)</div>', unsafe_allow_html=True)
                cropped_optimized = optimized_img.crop((left, top, right, bottom))
                st.image(cropped_optimized.resize((400, 400), Image.Resampling.NEAREST), use_container_width=True)

    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: var(--text-secondary); font-size: 0.85rem;">
        Зроблено з 💜 • Ваші файли не зберігаються на сервері
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
