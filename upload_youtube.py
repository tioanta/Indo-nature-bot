import os
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def generate_ai_caption(topic):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return f"Amazing View: {topic} 🌍 #Shorts", f"Beautiful nature scenery in {topic}. #Travel"
        
    genai.configure(api_key=api_key)
    
    # --- BAGIAN BARU: AUTO-DETECT MODEL ---
    print("   🤖 Sedang mencari model AI yang tersedia...")
    chosen_model = None
    
    try:
        # Minta daftar semua model yang tersedia di akun ini
        for m in genai.list_models():
            # Cari model yang bisa 'generateContent'
            if 'generateContent' in m.supported_generation_methods:
                # Prioritaskan model 'flash' (cepat) atau 'pro'
                if 'flash' in m.name:
                    chosen_model = m.name
                    break
                elif 'pro' in m.name and not chosen_model:
                    chosen_model = m.name
        
        # Jika loop selesai tapi belum dapet yang flash/pro, ambil apa saja yg pertama
        if not chosen_model:
             for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    chosen_model = m.name
                    break
                    
        if chosen_model:
            print(f"   ✅ Model ditemukan: {chosen_model}")
        else:
            raise Exception("Tidak ada model AI yang aktif di akun ini.")

        # --- MULAI GENERATE ---
        model = genai.GenerativeModel(chosen_model)
        
        prompt = f"""
        Kamu adalah Travel Influencer.
        Buatkan Judul dan Deskripsi YouTube Shorts tentang: {topic}.
        
        Aturan:
        1. Judul: Clickbait, Max 60 char, Emoji Bendera Negara.
        2. Deskripsi: 2 kalimat memuji keindahan.
        3. Hashtags: 3-5 tags relevan.
        4. Output WAJIB JSON murni: {{"title": "...", "description": "..."}}
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        return data['title'], data['description']

    except Exception as e:
        print(f"   ⚠️ Gagal Generate AI: {e}")
        print("   -> Menggunakan caption manual cadangan.")
        return f"Wanderlust: {topic} ✈️ #Shorts", f"Explore the beauty of {topic}. #Nature #Travel"

def upload_video(file_path, topic):
    # 1. Generate Caption
    print(f"AI sedang menulis caption untuk: {topic}...")
    title_ai, desc_ai = generate_ai_caption(topic)
    
    print(f"Judul Final: {title_ai}")

    # 2. Upload ke YouTube
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_json:
        raise Exception("Token YouTube tidak ditemukan")

    creds_dict = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_dict)

    youtube = build('youtube', 'v3', credentials=creds)

    request_body = {
        'snippet': {
            'title': title_ai,
            'description': desc_ai,
            'tags': ['Travel', 'Nature', 'Shorts', topic, 'Wanderlust'],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media
    )

    response = request.execute()
    print(f"🎉 SUKSES! Video uploaded ID: {response['id']}")
