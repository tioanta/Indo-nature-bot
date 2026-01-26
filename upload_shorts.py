import os
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def generate_caption(topic):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return f"{topic} #Shorts", "Enjoy the vibes! #Shorts #Video"
    
    genai.configure(api_key=api_key)
    
    print(f"   🤖 Gemini: Membuat Caption Shorts untuk {topic}...")
    
    # Auto-detect available model
    try:
        all_models = list(genai.list_models())
        valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # Try priority: gemini-2.0-flash > gemini-1.5-flash > gemini-pro > first available
        chosen_model = None
        for priority_model in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']:
            for m in valid_models:
                if priority_model in m:
                    chosen_model = m
                    break
            if chosen_model:
                break
        
        if not chosen_model and valid_models:
            chosen_model = valid_models[0]
        
        if not chosen_model:
            print("   ⚠️ Tidak ada model yang tersedia, gunakan fallback")
            return f"{topic} #Shorts", "Enjoy the vibes! #Shorts #Video"
        
        print(f"   Using model: {chosen_model}")
        model = genai.GenerativeModel(chosen_model)
    except Exception as e:
        print(f"   ⚠️ Error detect model: {e}, gunakan fallback")
        return f"{topic} #Shorts", "Enjoy the vibes! #Shorts #Video"
    
    prompt = f"""
    Kamu adalah expert YouTube Shorts. Buatkan Metadata untuk video pendek tentang: "{topic}".
    
    Gaya Bahasa:
    - Jika tentang Manchester United: Semangat, Fanatik, Glory Glory Man Utd.
    - Jika tentang Masjidil Haram: Islami, Menyejukkan hati, Masya Allah.
    - Jika tentang Japan: Aesthetic, Vibe tenang, Travel goals.
    
    Output JSON WAJIB:
    {{
        "title": "Judul clickbait pendek (<50 char) + #Shorts",
        "description": "Caption menarik 2 kalimat ajakan + 3-4 hashtags relevan"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data['title'], data['description']
    except Exception as e:
        print(f"   ⚠️ Generate caption error: {e}")
        return f"{topic} #Shorts", "Enjoy the vibes! #Shorts #Video"

def upload_video(file_path, topic):
    title, desc = generate_caption(topic)
    print(f"   Judul: {title}")
    
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    creds = Credentials.from_authorized_user_info(json.loads(token_json))
    youtube = build('youtube', 'v3', credentials=creds)

    body = {
        'snippet': {
            'title': title,
            'description': desc,
            'tags': ["Shorts", "Vertical", "Vibes", topic],
            'categoryId': '10' # Music/Entertainment
        },
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }

    youtube.videos().insert(
        part='snippet,status', body=body,
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    ).execute()
