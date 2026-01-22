import os
import json
import random
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_manual_caption(topic):
    """Caption cadangan jika AI mati total"""
    emojis = ["🔥", "✨", "😱", "🔴", "✅"]
    
    if "soccer" in topic.lower() or "football" in topic.lower():
        return f"Momen Gila Sepakbola! {topic} ⚽ {random.choice(emojis)}", f"Aksi terbaik {topic} hari ini. Jangan lupa subscribe! #Football #Shorts"
    elif "anime" in topic.lower() or "japan" in topic.lower():
        return f"Jepang Keren Banget! {topic} 🇯🇵 {random.choice(emojis)}", f"Suasana {topic} yang wajib kamu lihat. #Anime #Japan #Shorts"
    else:
        return f"Pemandangan Indah: {topic} 🌍 {random.choice(emojis)}", f"Healing sejenak melihat {topic}. #Nature #Travel #Shorts"

def generate_ai_caption(topic):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: 
        print("   ⚠️ API Key tidak ditemukan.")
        return get_manual_caption(topic)
        
    genai.configure(api_key=api_key)
    
    print(f"   🤖 Menghubungi Google AI untuk topik: {topic}...")
    
    # --- FITUR BARU: AUTO-DETECT MODEL ---
    # Script tidak akan menebak nama model, tapi minta daftar yang tersedia.
    chosen_model_name = None
    
    try:
        # Minta daftar model dari Google
        all_models = list(genai.list_models())
        
        # Cari model yang bisa generate text ('generateContent')
        valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        if valid_models:
            print(f"   ℹ️ Model yang tersedia di akun Anda: {valid_models}")
            
            # Prioritas 1: Cari yang ada kata 'flash' (Cepat)
            chosen_model_name = next((m for m in valid_models if 'flash' in m), None)
            
            # Prioritas 2: Cari yang ada kata 'pro' (Stabil)
            if not chosen_model_name:
                chosen_model_name = next((m for m in valid_models if 'pro' in m), None)
                
            # Prioritas 3: Ambil apa saja yang ada
            if not chosen_model_name:
                chosen_model_name = valid_models[0]
                
            print(f"   ✅ Memilih model otomatis: {chosen_model_name}")
        else:
            print("   ⚠️ Akun Google ini belum mengaktifkan layanan Generative AI (Model list kosong).")
            raise Exception("List model kosong")

        # --- MULAI GENERATE ---
        model = genai.GenerativeModel(chosen_model_name)
        
        prompt = f"""
        Kamu adalah YouTuber profesional. Topik: "{topic}".
        Buatkan Judul (Max 60 char, Clickbait, Emoji) dan Deskripsi (2 kalimat seru + Hashtags).
        Output WAJIB JSON: {{"title": "...", "description": "..."}}
        Peran: Jika bola jadilah komentator, jika alam jadilah puitis, jika anime jadilah wibu.
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        return data['title'], data['description']

    except Exception as e:
        print(f"   ❌ AI Gagal: {e}")
        print("   -> Menggunakan caption manual.")
        return get_manual_caption(topic)

def upload_video(file_path, topic):
    # 1. Generate Caption
    title_ai, desc_ai = generate_ai_caption(topic)
    print(f"Judul Final: {title_ai}")

    # 2. Upload
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_json:
        raise Exception("Token YouTube tidak ditemukan")

    try:
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
        youtube = build('youtube', 'v3', credentials=creds)

        body = {
            'snippet': {
                'title': title_ai,
                'description': desc_ai,
                'tags': ['Shorts', topic, 'Viral'],
                'categoryId': '22'
            },
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
        }

        youtube.videos().insert(
            part='snippet,status', body=body,
            media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
        ).execute()
        print(f"🎉 SUKSES UPLOAD VIDEO!")
        
    except Exception as e:
        # Menangkap error kuota habis agar tidak panik
        if "exceeded" in str(e) or "quota" in str(e):
            print("\n🚨 KUOTA UPLOAD HARI INI HABIS! (Limit Harian Google)")
            print("Video sudah dibuat tapi tidak bisa diupload sekarang.")
            print("Bot akan mencoba lagi besok secara otomatis.")
        else:
            print(f"❌ Error Upload: {e}")
