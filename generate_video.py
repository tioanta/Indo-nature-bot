import os
import requests
import random
from moviepy.editor import VideoFileClip, AudioFileClip

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# Menggunakan Nama File Resmi di Wikimedia (Bukan Link Langsung)
# Script akan mencari link aslinya secara otomatis lewat API.
MUSIC_TITLES = [
    "File:Frederic_Chopin_-_Nocturne_Eb_major_Opus_9,_number_2.ogg",
    "File:Gymnopedie_No._1..ogg",
    "File:Clair_de_lune_(Claude_Debussy)_Suite_bergamasque.ogg"
]

def get_wikimedia_direct_url(title):
    """Mendapatkan Link Download Asli via API Wikimedia"""
    api_url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url",
        "titles": title
    }
    
    # Header User-Agent (Wajib agar tidak diblokir)
    headers = {
        'User-Agent': 'BotPencariAlam/1.0 (test@example.com)' 
    }

    try:
        response = requests.get(api_url, params=params, headers=headers)
        data = response.json()
        pages = data['query']['pages']
        for page_id in pages:
            if 'imageinfo' in pages[page_id]:
                return pages[page_id]['imageinfo'][0]['url']
    except Exception as e:
        print(f"   Gagal mengambil API untuk {title}: {e}")
    
    return None

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
    print("2. Mencari & Download Musik Latar (via API)...")
    
    # Header untuk download file
    headers = {
        'User-Agent': 'BotPencariAlam/1.0 (test@example.com)'
    }

    try:
        # Pilih 1 judul lagu
        chosen_title = random.choice(MUSIC_TITLES)
        print(f"   Lagu terpilih: {chosen_title}")
        
        # Minta Link Asli ke API
        music_url = get_wikimedia_direct_url(chosen_title)
        
        if not music_url:
            print("   Gagal mendapatkan URL dari API.")
            return None

        print(f"   Mengunduh dari URL Stabil: {music_url}")
        
        r = requests.get(music_url, headers=headers, stream=True)
        
        if r.status_code == 200:
            audio_filename = "bg_music.ogg"
            with open(audio_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # Validasi ukuran file
            if os.path.getsize(audio_filename) < 10000:
                print("   File audio korup/terlalu kecil.")
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
    
    try:
        video_clip = VideoFileClip(input_video_path)
    except Exception as e:
        print(f"Error membaca video: {e}")
        return None
    
    # 2. Potong durasi video (Max 15 detik)
    duration = min(video_clip.duration, 15) 
    video_clip = video_clip.subclip(0, duration)
    
    # 3. Crop ke 9:16 (Vertikal)
    if video_clip.w > video_clip.h:
        new_width = video_clip.h * 9 / 16
        x1 = (video_clip.w / 2) - (new_width / 2)
        video_clip = video_clip.crop(x1=x1, width=new_width, height=video_clip.h)
    
    # 4. Tambahkan Audio
    audio_path = get_background_music()
    final_clip = video_clip
    
    if audio_path:
        try:
            audio_clip = AudioFileClip(audio_path)
            
            # Loop audio jika kependekan
            if audio_clip.duration < duration:
                # Teknik looping manual yang aman
                from moviepy.audio.AudioClip import CompositeAudioClip
                loops = int(duration / audio_clip.duration) + 1
                audio_clip = CompositeAudioClip([audio_clip.set_start(i * audio_clip.duration) for i in range(loops)])
            
            audio_clip = audio_clip.subclip(0, duration)
            audio_clip = audio_clip.volumex(0.8) # Volume 80%
            
            final_clip = video_clip.set_audio(audio_clip)
            print("   Sukses menggabungkan Audio + Video.")
            
        except Exception as e:
            print(f"   Error saat merging audio: {e}. Video akan bisu.")
    else:
        print("   Audio tidak tersedia. Video akan bisu.")

    # 5. Render Final
    print("3. Rendering Final Video...")
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    # Cleanup
    try:
        video_clip.close()
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
    except:
        pass
        
    return output_file
