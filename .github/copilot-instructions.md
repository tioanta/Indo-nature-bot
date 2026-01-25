# Indo-Nature Bot: AI Coding Instructions

## Project Overview
This is a **YouTube Music & Relaxation Automation Bot** that generates, creates, and uploads long-form music videos (10 minutes each) focused on relaxing and focusing content across three music genres (Lofi/Study, Meditation/Relaxation, and Nature Sounds) using free/affordable APIs (Wikimedia Commons for audio, Google Generative AI for captions).

**Architecture**: Three sequential modules orchestrated by `main.py`:
1. **`generate_video.py`**: Fetch relaxing music from Wikimedia Commons API → Create animated background visual with topic text → Format as 1920x1080 landscape video
2. **`upload_youtube.py`**: Generate AI-written captions (YouTube title + description optimized for music) → Upload via Google YouTube API with appropriate music/wellness categories
3. **`main.py`**: Orchestrates workflow with random music topic selection and error handling

## Critical Patterns & Workflows

### 1. Topic-Driven Behavior (Fundamental Design)
The **topic string** flows through the entire pipeline and determines music styling:
- **Content type detection**: `get_relaxing_music(topic)` uses `topic.lower()` to detect "lofi"/"study"/"focus", "meditation"/"sleep"/"zen", or default to nature sounds
- **Music keywords**: Each genre gets specific search keywords (lofi hip hop for study, meditation ambient for relaxation, nature sounds/rain for nature)
- **AI caption generation**: `generate_ai_caption(topic)` receives topic to craft appropriate persona (productivity focus for study music, calming tone for meditation, natural/ambient for nature sounds)
- **YouTube category & tags**: Dynamic selection of category ID (10=Music, 39=Wellness) and tags based on topic keywords
- **Pass topic to all functions**: Ensure consistency across music/visual/upload stages (see `main.py` showing `topic=today_topic` parameter)

### 2. External API Management & Fallback Strategies
Two primary APIs with different characteristics:
- **Wikimedia Commons API** (`get_wikimedia_search_url`): Free, no authentication required; returns OGG audio files; custom user-agent header required; gracefully handles partial results with `random.choice()`
- **Google Generative AI** (`generate_ai_caption`): **Auto-detects available model** (priority: flash > pro > first available); gracefully falls back to `get_manual_caption()` template if API key missing or quota exhausted

### 3. Video Format Transformation
**Current Format:**
- **Format**: Landscape 1920x1080 (16:9), 10 minutes (600 seconds), audio-primary content
- **Visual approach**: Animated background with moving orbs and waves + topic text overlay
- **Audio focus**: Music IS the primary content; animated visuals are secondary
- **Duration handling**: If music is shorter than 10 minutes, `concatenate_audioclips()` loops the audio to fill the full duration
- **FPS Optimization**: Renders at 12 FPS (optimized for speed) instead of 24 FPS

### 4. Error Handling Philosophy
- **Silent failures with fallbacks**: `try/except` blocks pass silently or return `None` rather than crash
- **Quota-aware uploads**: Detects "exceeded" or "quota" in error messages to handle daily YouTube upload limits gracefully
- **Audio fallback**: If music retrieval fails, still attempt upload (though will fail without audio)

### 5. Environment Variables Required
```
PEXELS_API_KEY=<not_used_anymore>  (legacy, can be empty)
GEMINI_API_KEY=<google_gemini_api_key>
YOUTUBE_TOKEN_JSON=<json_string_of_oauth_credentials>
```
Token must be valid JSON string; loaded via `json.loads()` in `upload_youtube.py`

## Common Modifications
- **Add new music genre**: Update topics list in `main.py` (must include genre keywords like "lofi", "meditation", or "nature") and add matching keyword detection in `get_relaxing_music()` to route music selection correctly
- **Adjust video length**: Change `duration=600` in `create_music_video()` (currently 10 minutes = 600 seconds); affects rendering time significantly
- **Change background colors**: Modify RGB tuples in `make_animated_background()` function (currently: study=dark blue, meditation=dark teal, nature=deep blue)
- **Customize AI captions**: Edit the prompt in `generate_ai_caption()` to change tone/keywords (currently optimized for relaxing music industry standards)
- **Change audio source**: Replace Wikimedia with another free audio API by modifying `get_relaxing_music()` function
- **Adjust rendering speed**: Change FPS value (default 12) in both `make_animated_background()` and `write_videofile()` call

## Testing Workflow
No automated tests present. Manual validation required:
1. Set env vars locally: `GEMINI_API_KEY` and `YOUTUBE_TOKEN_JSON` (PEXELS_API_KEY no longer needed)
2. Run `python main.py` and verify all three stages (music fetch, video creation, upload)
3. Check YouTube channel for up10 minutes
   - Background has animated orbs and wavesimately 20 minutes
   - Background is dark with topic text visible
   - Category is either "Music" or "Wellness"
   - Tags and descriptions are music-focused (not sports/entertainment)
   - Audio quality is preserved (no distortion)
