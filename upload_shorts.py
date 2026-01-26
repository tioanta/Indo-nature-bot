import os
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def generate_caption(topic):
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    print(f"   🤖 Gemini: Membuat Caption Shorts untuk {topic}...")
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
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
    except:
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
