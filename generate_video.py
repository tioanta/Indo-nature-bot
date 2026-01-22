import os
import requests
import random
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# Daftar Musik Aman (Public Domain / Creative Commons)
# Kita gunakan link stabil dari Wikimedia Commons & Sumber Free lainnya
MUSIC_URLS = [
    # Erik Satie - Gymnopedie No 1 (Sangat cocok untuk nature/calm)
    "https://upload.wikimedia.org/wikipedia/commons/e/e6/Erik_Satie_-_Gymnopedie_No_1.ogg",
    # Chopin - Nocturne (Piano lembut)
    "https://upload.wikimedia.org/wikipedia/commons/e/e3/Frederic_Chopin_-_Nocturne_in_E_flat_major%2C_Op._9%2C_No._2.ogg",
    # Debussy - Clair de Lune
    "https://upload.wikimedia.org/wikipedia/commons/3/36/Claude_Debussy_-_Clair_de_lune.ogg",
    # Lagu Alam / Ambient (Contoh placeholder, jika gagal akan pakai yang atas)
    "https://upload.wikimedia.org/wikipedia/commons/7/73/Kawai-calm.ogg"
]

def get_pexels_video(topic="Nature Scenery", orientation="portrait"):
    headers = {"Authorization": PEXELS_API_KEY}
    
    print(f"1. Searching Pexels for: {topic}")
    url = f"https://api.pexels.com/videos/search?query={topic}&per_page=15&orientation={orientation}"
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception as e:
        print(f"Error connecting to Pexels: {e}")
        return None
    
    if not data.get('videos'):
        print(f"Video tidak ditemukan untuk: {topic}")
        return None

    # Pilih video random
    video_data = random.choice(data['videos'])
    video_files = video_data['video_files']
    
    # Prioritaskan HD (width >= 720)
    valid_files = [v for v in video_files if v['width'] >= 720]
    if not valid_files:
        valid_files = video_files 
        
    chosen_file = valid_files[0]
    download_url = chosen_file['link']
    
    print(f"   Downloading video...")
    r = requests.get(download_url)
    video_filename = "input_video.mp4"
    with open(video_filename, 'wb') as f:
        f.write(r.content)
        
    return video_filename

def get_background_music():
    print("2. Mencari & Download Musik Latar...")
    try:
        # Pilih 1 lagu secara acak
        music_url = random.choice(MUSIC_URLS)
        
        r = requests.get(music_url)
        audio_filename = "bg_music.ogg" # Format OGG lebih ringan & didukung moviepy
        with open(audio_filename, 'wb') as f:
            f.write(r.content)
        return audio_filename
    except Exception as e:
        print(f"   Gagal download musik: {e}")
        return None

def process_video(input_video_path):
    output_file = "final_short.mp4"
    
    # 1. Load Video
    video_clip = VideoFileClip(input_video_path)
    
    # 2. Potong durasi video (Max 15 detik untuk Shorts)
    duration = min(video_clip.duration, 15) 
    video_clip = video_clip.subclip(0, duration)
    
    # 3. Crop ke 9:16 (Vertikal)
    if video_clip.w > video_clip.h:
        video_clip = video_clip.crop(x1=video_clip.w/2 - video_clip.h*9/32, width=video_clip.h*9/16, height=video_clip.h)
    
    # 4. Tambahkan Audio
    audio_path = get_background_music()
    if audio_path:
        try:
            # Load Audio
            audio_clip = AudioFileClip(audio_path)
            
            # Jika lagu lebih pendek dari video, di-loop (jarang terjadi sih)
            if audio_clip.duration < duration:
                from moviepy.audio.fx.all import audio_loop
                audio_clip = audio_loop(audio_clip, duration=duration)
            
            # Potong audio sesuai durasi video
            audio_clip = audio_clip.subclip(0, duration)
            
            # Set volume (biar tidak terlalu kencang/pecah) -> 80%
            audio_clip = audio_clip.volumex(0.8)
            
            # Tempel ke video
            video_clip = video_clip.set_audio(audio_clip)
            print("   Sukses menggabungkan Audio + Video.")
        except Exception as e:
            print(f"   Error saat merging audio: {e} (Video akan bisu)")
    
    # 5. Render Final
    print("3. Rendering Final Video...")
    # audio_codec='aac' wajib agar suara keluar di YouTube/HP
    video_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
    
    return output_file
