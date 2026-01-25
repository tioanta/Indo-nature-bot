import os
import json
import random
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_manual_caption(topic):
    """Caption cadangan jika AI mati total - untuk konten musik relaxing"""
    emojis = ["🎵", "😌", "✨", "🧘", "🎧"]
    
    topic_lower = topic.lower()
    if "lofi" in topic_lower or "study" in topic_lower or "focus" in topic_lower or "work" in topic_lower:
        return f"{topic} 🎧 {random.choice(emojis)}", f"Musik berkualitas untuk fokus dan produktivitas 20 menit. Subscribe untuk lebih banyak konten! #LofiBeats #StudyMusic #FocusMusic"
    elif "meditation" in topic_lower or "sleep" in topic_lower or "relax" in topic_lower or "zen" in topic_lower:
        return f"{topic} 🧘 {random.choice(emojis)}", f"Musik meditasi dan relaksasi untuk istirahat. Sempurna untuk tidur dan stress relief. #MeditationMusic #RelaxingMusic #SleepMusic"
    else:
        return f"{topic} 🌿 {random.choice(emojis)}", f"Suara alam untuk ketenangan dan healing 20 menit. Subscribe untuk konten relaxing lainnya! #NatureSounds #AmbientMusic #CalmMusic"

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
        Kamu adalah content creator musik relaxing & fokus profesional untuk YouTube.
        Topik: "{topic}" (durasi 20 menit).
        
        Buatkan Judul (Max 60 char dengan emoji musik) dan Deskripsi (2-3 kalimat + hashtags relaksasi/fokus).
        
        Output WAJIB JSON: {{"title": "...", "description": "..."}}
        
        Instruksi konten:
        - Jika topik mengandung: lofi/study/focus/work → jadilah musik untuk belajar (motivasi, produktivitas)
        - Jika topik mengandung: meditation/sleep/zen/relax → jadilah musik untuk meditasi/tidur (menenangkan, healing)
        - Jika topik mengandung: nature/rain/forest/ocean → jadilah ambient (natural, menenangkan)
        - Gunakan emoji musik (🎵🎧😌🧘✨) untuk deskripsi
        - Sertakan hashtag yang relevan seperti #LofiBeats #StudyMusic #MeditationMusic #RelaxingMusic
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

        # Tentukan category ID berdasarkan topic
        # YouTube valid categories: 10=Music, 17=Sports, 18=Short Movies, 20=Shorts, 21=Trailers, 
        # 22=Videos, 23=Watches, 24=World, 25=Animation, 26=Autos, 27=Blooper, 28=Children, 
        # 29=Comedy, 30=Documentaries, 31=Education, 32=Entertainment, 33=Events, 34=Film, 
        # 35=Gaming, 36=Holiday, 37=How-To, 38=Human, 39=INVALID, 40=Import, 41=Interaction, 42=Internship
        topic_lower = topic.lower()
        if any(word in topic_lower for word in ['lofi', 'study', 'focus', 'work', 'meditation', 'sleep', 'relax', 'zen', 'nature', 'ambient']):
            category_id = '10'  # Music category (valid)
        else:
            category_id = '10'  # Default to Music (safest option)
        
        # Tentukan tags berdasarkan topic
        default_tags = ['Music', 'Relaxing', '10 minutes']
        if 'lofi' in topic_lower or 'study' in topic_lower:
            tags = default_tags + ['LofiBeats', 'StudyMusic', 'FocusMusic']
        elif 'meditation' in topic_lower or 'sleep' in topic_lower:
            tags = default_tags + ['MeditationMusic', 'SleepMusic', 'Relaxation']
        else:
            tags = default_tags + ['AmbientMusic', 'NatureSounds', 'CalmMusic']
        
        body = {
            'snippet': {
                'title': title_ai,
                'description': desc_ai,
                'tags': tags,
                'categoryId': category_id
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
