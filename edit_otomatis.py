"""
Robot Editor - Script edit video/foto otomatis
Didesain untuk dijalankan di Google Colab, dengan folder input/output di Google Drive.

Struktur folder yang dibutuhkan di Google Drive:
  MyDrive/RobotEditor/input/    -> taruh video mentah di sini (.mp4, .mov)
  MyDrive/RobotEditor/output/   -> hasil video jadi otomatis muncul di sini
  MyDrive/RobotEditor/musik/backsound.mp3  -> (opsional) musik latar
"""

import os
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip,
    AudioFileClip, CompositeAudioClip
)
import whisper

# ==== KONFIGURASI PATH (Google Drive) ====
BASE_DIR = "/content/drive/MyDrive/RobotEditor"
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
MUSIK = os.path.join(BASE_DIR, "musik", "backsound.mp3")

# Buat folder otomatis kalau belum ada
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MUSIK), exist_ok=True)

# Load model whisper sekali saja (biar tidak lambat kalau banyak file)
_model_whisper = None
def get_model():
    global _model_whisper
    if _model_whisper is None:
        print("Memuat model Whisper (auto-caption)...")
        _model_whisper = whisper.load_model("base")
    return _model_whisper

def buat_caption(video_path):
    model = get_model()
    hasil = model.transcribe(video_path, fp16=False)
    return hasil["segments"]

def edit_video(nama_file):
    path_video = os.path.join(INPUT_DIR, nama_file)
    clip = VideoFileClip(path_video)

    # 1. Resize otomatis ke format vertikal (9:16) untuk Reels/TikTok/Shorts
    clip_vertikal = clip.resize(height=1920)
    if clip_vertikal.w > 1080:
        clip_vertikal = clip_vertikal.crop(x_center=clip_vertikal.w / 2, width=1080)

    # 2. Auto caption dari suara (Whisper)
    print(f"  -> Membuat caption otomatis untuk {nama_file} ...")
    segments = buat_caption(path_video)
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

    # 3. Gabungkan video + caption
    video_final = CompositeVideoClip([clip_vertikal] + teks_klip)

    # 4. Tambah musik latar (volume dikecilkan), opsional
    if os.path.exists(MUSIK):
        musik = AudioFileClip(MUSIK).volumex(0.15)
        if musik.duration < video_final.duration:
            musik = musik.loop(duration=video_final.duration)
        else:
            musik = musik.subclip(0, video_final.duration)
        if video_final.audio is not None:
            audio_gabung = CompositeAudioClip([video_final.audio, musik])
        else:
            audio_gabung = musik
        video_final = video_final.set_audio(audio_gabung)

    # 5. Simpan hasil
    output_path = os.path.join(OUTPUT_DIR, f"edited_{nama_file}")
    print(f"  -> Menyimpan hasil ke {output_path}")
    video_final.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")

    clip.close()
    video_final.close()

def sudah_diedit(nama_file):
    return os.path.exists(os.path.join(OUTPUT_DIR, f"edited_{nama_file}"))

def main():
    daftar_file = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith((".mp4", ".mov"))]
    if not daftar_file:
        print("Tidak ada video baru di folder input/.")
        return

    for file in daftar_file:
        if sudah_diedit(file):
            print(f"Lewati (sudah pernah diedit): {file}")
            continue
        print(f"Mengedit: {file}")
        try:
            edit_video(file)
        except Exception as e:
            print(f"  GAGAL edit {file}: {e}")

    print("Selesai! Cek folder output/ di Google Drive kamu.")

if __name__ == "__main__":
    main()
