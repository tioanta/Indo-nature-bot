import os
import requests
import random
from moviepy.editor import VideoFileClip, AudioFileClip

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# Daftar Musik Aman (Wikimedia)
MUSIC_URLS = [
    "https://upload.wikimedia.org/wikipedia/commons/e/e6/Erik_Satie_-_Gymnopedie_No_1.ogg",
    "https://upload.wikimedia.org/wikipedia/commons/e/e3/Frederic_Chopin_-_Nocturne_in_E_flat_major%2C_Op._9%2C_No._2.ogg",
    "https://upload.wikimedia.org/wikipedia/commons/3/36/Claude_Debussy_-_Clair_de_lune.ogg"
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
    
    # HEADER PENTING: Agar tidak diblokir Wikimedia
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        music_url = random.choice(MUSIC_URLS)
        print(f"   Mengunduh dari: {music_url}")
        
        r = requests.get(music_url, headers=headers, stream=True)
        
        # Cek apakah download sukses (Kode 200)
        if r.status_code == 200:
            audio_filename = "bg_music.ogg"
            with open(audio_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # Cek ukuran file, kalau terlalu kecil (< 10KB) berarti error
            if os.path.getsize(audio_filename) < 10000:
                print("   File audio korup/terlalu kecil. Skip audio.")
                return None
                
            return audio_filename
        else:
            print(f"   Gagal download. Status Code: {r.status_code}")
            return None

    except Exception as e:
        print(f"   Gagal download musik: {e}")
        return None

def process_video(input_video_path):
    output_file = "final_short.mp4"
    
    # 1. Load Video
    try:
        video_clip = VideoFileClip(input_video_path)
    except OSError:
        print("Error: File video rusak atau tidak terbaca.")
        return None
    
    # 2. Potong durasi video (Max 15 detik)
    duration = min(video_clip.duration, 15) 
    video_clip = video_clip.subclip(0, duration)
    
    # 3. Crop ke 9:16 (Vertikal)
    if video_clip.w > video_clip.h:
        # Crop tengah
        new_width = video_clip.h * 9 / 16
        x1 = (video_clip.w / 2) - (new_width / 2)
        video_clip = video_clip.crop(x1=x1, width=new_width, height=video_clip.h)
    
    # 4. Tambahkan Audio
    audio_path = get_background_music()
    final_clip = video_clip # Default tanpa suara
    
    if audio_path:
        try:
            # Load Audio
            audio_clip = AudioFileClip(audio_path)
            
            # Loop audio jika lebih pendek dari video
            if audio_clip.duration < duration:
                # Manual loop sederhana untuk kompatibilitas moviepy lama
                from moviepy.audio.AudioClip import CompositeAudioClip
                audio_clip = CompositeAudioClip([audio_clip.set_start(i*audio_clip.duration) for i in range(int(duration/audio_clip.duration)+1)])
            
            # Potong audio sesuai durasi video
            audio_clip = audio_clip.subclip(0, duration)
            
            # Set volume 80%
            audio_clip = audio_clip.volumex(0.8)
            
            # Tempel ke video
            final_clip = video_clip.set_audio(audio_clip)
            print("   Sukses menggabungkan Audio + Video.")
            
        except Exception as e:
            print(f"   Error saat merging audio: {e}. Video akan bisu.")
            final_clip = video_clip # Fallback ke video bisu
    else:
        print("   Audio tidak ditemukan/gagal download. Video akan bisu.")

    # 5. Render Final
    print("3. Rendering Final Video...")
    # Gunakan preset ultrafast agar hemat waktu runner
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    # Bersihkan file sampah
    try:
        video_clip.close()
        if audio_path: 
            # Hapus file audio temp
            os.remove(audio_path)
    except:
        pass
        
    return output_file
