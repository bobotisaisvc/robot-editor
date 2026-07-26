import streamlit as st
import tempfile
import os
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip,
    AudioFileClip, CompositeAudioClip
)

st.set_page_config(page_title="Robot Editor Video", page_icon="🤖", layout="centered")

st.title("🤖 Robot Editor Video Otomatis")
st.write("Upload video kamu, robot akan otomatis: resize ke format vertikal, tambah caption (opsional), dan tambah musik latar (opsional).")

# ==== INPUT DARI USER ====
video_file = st.file_uploader("1. Upload video (.mp4 / .mov)", type=["mp4", "mov"])
musik_file = st.file_uploader("2. (Opsional) Upload musik latar (.mp3)", type=["mp3"])

try:
    import whisper  # noqa: F401
    WHISPER_TERSEDIA = True
except ImportError:
    WHISPER_TERSEDIA = False

if WHISPER_TERSEDIA:
    pakai_caption = st.checkbox("Tambahkan auto-caption dari suara (proses lebih lama)", value=False)
else:
    st.info("Fitur auto-caption belum aktif di versi ringan ini (supaya instalasi lebih stabil). Resize video & musik latar tetap berfungsi normal.")
    pakai_caption = False

proses_btn = st.button("🚀 Proses Video", type="primary", disabled=(video_file is None))

def buat_caption(video_path):
    import whisper
    model = whisper.load_model("base")
    hasil = model.transcribe(video_path, fp16=False)
    return hasil["segments"]

def edit_video(path_video_input, path_musik, pakai_caption, progress_callback):
    clip = VideoFileClip(path_video_input)
    progress_callback(0.2, "Resize ke format vertikal 9:16...")

    clip_vertikal = clip.resize(height=1920)
    if clip_vertikal.w > 1080:
        clip_vertikal = clip_vertikal.crop(x_center=clip_vertikal.w / 2, width=1080)

    video_final = clip_vertikal

    if pakai_caption:
        progress_callback(0.4, "Membuat caption otomatis (Whisper AI)...")
        segments = buat_caption(path_video_input)
        teks_klip = []
        for seg in segments:
            txt = TextClip(
                seg["text"].strip(), fontsize=48, color='white',
                font='DejaVu-Sans-Bold', stroke_color='black', stroke_width=2,
                method='caption', size=(clip_vertikal.w * 0.9, None)
            )
            txt = txt.set_position(('center', 0.82), relative=True)
            txt = txt.set_start(seg["start"]).set_end(seg["end"])
            teks_klip.append(txt)
        video_final = CompositeVideoClip([clip_vertikal] + teks_klip)

    if path_musik:
        progress_callback(0.7, "Menambahkan musik latar...")
        musik = AudioFileClip(path_musik).volumex(0.15)
        if musik.duration < video_final.duration:
            musik = musik.loop(duration=video_final.duration)
        else:
            musik = musik.subclip(0, video_final.duration)
        if video_final.audio is not None:
            audio_gabung = CompositeAudioClip([video_final.audio, musik])
        else:
            audio_gabung = musik
        video_final = video_final.set_audio(audio_gabung)

    progress_callback(0.85, "Menyimpan video hasil...")
    output_path = os.path.join(tempfile.gettempdir(), "hasil_edit.mp4")
    video_final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", logger=None)

    clip.close()
    video_final.close()
    return output_path

if proses_btn and video_file is not None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path_video_input = os.path.join(tmp_dir, video_file.name)
        with open(path_video_input, "wb") as f:
            f.write(video_file.read())

        path_musik = None
        if musik_file is not None:
            path_musik = os.path.join(tmp_dir, musik_file.name)
            with open(path_musik, "wb") as f:
                f.write(musik_file.read())

        progress_bar = st.progress(0, text="Memulai proses...")

        def update_progress(value, text):
            progress_bar.progress(value, text=text)

        try:
            with st.spinner("Robot sedang bekerja, mohon tunggu..."):
                output_path = edit_video(path_video_input, path_musik, pakai_caption, update_progress)
            progress_bar.progress(1.0, text="Selesai!")
            st.success("Video berhasil diedit!")

            with open(output_path, "rb") as f:
                st.video(f.read())
            with open(output_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Video Hasil Edit",
                    data=f,
                    file_name="hasil_edit.mp4",
                    mime="video/mp4"
                )
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses video: {e}")

st.markdown("---")
st.caption("Catatan: Server gratis ini punya RAM & CPU terbatas. Untuk hasil terbaik, gunakan video pendek (di bawah 1-2 menit).")
