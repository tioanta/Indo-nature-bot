import os
import requests
import random
from moviepy.editor import VideoFileClip, AudioFileClip

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# --- UPDATE BESAR DISINI ---
# Kita perbanyak kata kuncinya agar musiknya ganti-ganti terus.
# Bot akan memilih 1 genre secara acak setiap kali jalan.
MUSIC_KEYWORDS = [
    # Klasik Populer (Aman & Tenang)
    "Erik Satie Gymnopedie No 1 ogg",
    "Chopin Nocturne Op 9 No 2 ogg",
    "Debussy Clair de Lune ogg",
    "Beethoven Moonlight Sonata ogg",
    "Bach Cello Suite No 1 ogg",
    "Mozart Piano Sonata 16 ogg",
    "Vivaldi Four Seasons Spring ogg",
    
    # Ambient & Nature (Suara Alam/Meditasi)
    "Relaxing piano music ogg",
    "Ambient synthesizer music ogg",
    "Meditation music ogg",
    "Cinematic atmosphere music ogg",
    
    # Instrumen Lain
    "Acoustic guitar relaxing ogg",
    "Harp music classical ogg",
    "Flute relaxing music ogg"
]

def get_wikimedia_search_url(query):
    """Mencari URL Audio via Fitur Pencarian Wikimedia"""
    api_url = "https://commons.wikimedia.org/w/api.php"
    
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,      
        "gsrnamespace": 6,       # Namespace File
        "gsrlimit": 3,           # Ambil 3 hasil teratas (biar variatif)
        "prop": "imageinfo",     
        "iiprop": "url"          
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' 
    }

    try:
        response = requests.get(api_url, params=params, headers=headers)
        data = response.json()
        
        # Ambil hasil random dari 3 teratas (biar gak selalu ambil nomor 1)
        if "query" in data and "pages" in data["query"]:
            pages = list(data["query"]["pages"].values())
            if pages:
                chosen_page = random.choice(pages) # Random pick
                if "imageinfo" in chosen_page:
                    return chosen_page["imageinfo"][0]["url"]
    except Exception as e:
        print(f"   Gagal mencari API untuk {query}: {e}")
    
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
    print("2. Mencari & Download Musik Latar (Mode DJ Random)...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # 1. Pilih Genre secara acak dari daftar panjang
        # Kita copy listnya dan acak biar urutannya beda-beda tiap hari
        shuffled_keywords = random.sample(MUSIC_KEYWORDS, len(MUSIC_KEYWORDS))
        
        for keyword in shuffled_keywords:
            print(f"   Mencoba mencari lagu: '{keyword}'")
            music_url = get_wikimedia_search_url(keyword)
            
            if not music_url:
                print("   Zonk, coba genre lain...")
                continue

            print(f"   URL didapat, mulai download...")
            r = requests.get(music_url, headers=headers, stream=True)
            
            if r.status_code == 200:
                audio_filename = "bg_music.ogg"
                with open(audio_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                
                # Validasi ukuran (Minimal 20KB biar bukan sound effect pendek)
                if os.path.getsize(audio_filename) > 20000:
                    print("   Download Musik Sukses!")
                    return audio_filename
                else:
                    print("   File terlalu kecil (mungkin cuma efek suara), cari yang lain...")
            
        return None

    except Exception as e:
        print(f"   Error sistem download musik: {e}")
        return None

def process_video(input_video_path):
    output_file = "final_short.mp4"
    
    try:
        video_clip = VideoFileClip(input_video_path)
    except Exception as e:
        print(f"Error membaca video: {e}")
        return None
    
    # Potong durasi video (Max 15 detik)
    duration = min(video_clip.duration, 15) 
    video_clip = video_clip.subclip(0, duration)
    
    # Crop ke 9:16 (Vertikal)
    if video_clip.w > video_clip.h:
        new_width = video_clip.h * 9 / 16
        x1 = (video_clip.w / 2) - (new_width / 2)
        video_clip = video_clip.crop(x1=x1, width=new_width, height=video_clip.h)
    
    # Tambah Audio
    audio_path = get_background_music()
    final_clip = video_clip
    
    if audio_path:
        try:
            audio_clip = AudioFileClip(audio_path)
            
            # Loop audio jika kependekan
            if audio_clip.duration < duration:
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

    print("3. Rendering Final Video...")
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", preset="ultrafast")
    
    # Bersih-bersih
    try:
        video_clip.close()
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
    except:
        pass
        
    return output_file
