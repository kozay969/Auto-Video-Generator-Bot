#!/usr/bin/env python3
"""
Step 0: YouTube Video မှ Transcript/Captions ထုတ်ပြီး Myanmar script အတွက် summarize မည်
"""

import argparse
import json
import os
import re
import sys
from openai import OpenAI


def extract_youtube_id(url: str) -> str:
    """YouTube URL မှ video ID ထုတ်မည်"""
    patterns = [
        r'(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Valid YouTube URL မဟုတ်ပါ: {url}")


def get_transcript_via_api(video_id: str) -> str:
    """youtube-transcript-api သုံးပြီး transcript ထုတ်မည်"""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api.formatters import TextFormatter

        # Try multiple languages
        langs_to_try = ['my', 'en', 'en-US', 'en-GB']

        transcript = None
        used_lang = None

        for lang in langs_to_try:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
                used_lang = lang
                print(f"  ✅ Transcript ရပြီ ({lang})")
                break
            except Exception:
                continue

        # Auto-generated fallback
        if not transcript:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for t in transcript_list:
                    transcript = t.fetch()
                    used_lang = t.language_code
                    print(f"  ✅ Auto transcript ရပြီ ({used_lang})")
                    break
            except Exception as e:
                print(f"  ⚠️ Transcript API error: {e}")
                return ""

        if not transcript:
            return ""

        formatter = TextFormatter()
        text = formatter.format_transcript(transcript)
        print(f"  📝 Transcript length: {len(text)} chars ({used_lang})")
        return text

    except ImportError:
        print("  ⚠️ youtube-transcript-api မရှိပါ")
        return ""


def get_video_metadata(video_id: str) -> dict:
    """yt-dlp သုံးပြီး video metadata ထုတ်မည်"""
    try:
        import subprocess
        result = subprocess.run([
            'yt-dlp',
            '--dump-json',
            '--no-playlist',
            '--skip-download',
            f'https://www.youtube.com/watch?v={video_id}'
        ], capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                'title': data.get('title', ''),
                'description': data.get('description', '')[:1000],  # First 1000 chars
                'duration': data.get('duration', 0),
                'channel': data.get('uploader', ''),
                'view_count': data.get('view_count', 0),
                'tags': data.get('tags', [])[:10],
            }
    except Exception as e:
        print(f"  ⚠️ Metadata error: {e}")

    return {'title': '', 'description': '', 'duration': 0, 'channel': '', 'tags': []}


def summarize_and_translate(
    transcript: str,
    metadata: dict,
    youtube_url: str,
    duration_minutes: int
) -> dict:
    """OpenRouter API သုံးပြီး transcript ကို Myanmar script အဖြစ် ပြန်ဆိုပြီး summarize မည်"""

    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1"
    )

    words_per_minute = 120
    target_words = words_per_minute * duration_minutes

    video_title = metadata.get('title', 'YouTube Video')
    description = metadata.get('description', '')
    channel = metadata.get('channel', '')

    # Build context from available info
    context_parts = []
    if video_title:
        context_parts.append(f"Video Title: {video_title}")
    if channel:
        context_parts.append(f"Channel: {channel}")
    if description:
        context_parts.append(f"Description: {description[:500]}")
    if transcript:
        # Limit transcript to avoid token overflow
        context_parts.append(f"Transcript:\n{transcript[:6000]}")

    context = "\n\n".join(context_parts)

    if not context.strip():
        raise ValueError("Video မှ content ထုတ်မရပါ - transcript နှင့် metadata မတွေ့ပါ")

    prompt = f"""သင်သည် မြန်မာဘာသာဖြင့် ဗီဒီယိုကြည့်ရှုသူများအတွက် engaging content ရေးသားသော expert တစ်ဦးဖြစ်သည်။

အောက်ပါ YouTube video content ကို မြန်မာဘာသာဖြင့် {duration_minutes} မိနစ်ကြာ ဗီဒီယိုအတွက် script ပြောင်းရေးပါ:

{context}

Source: {youtube_url}

လိုအပ်ချက်များ:
- Target word count: {target_words} words (မြန်မာဘာသာ)
- Video ၏ အဓိကအချက်များကို ဆွဲထုတ်ပါ
- မြန်မာပြည်သူ နားလည်လွယ်သော ဘာသာစကား သုံးပါ
- Original video ၏ အဓိပ္ပာယ်နှင့် insight များ ထိန်းသိမ်းပါ
- ပြောကြားသကဲ့သို့ သဘာဝကျကျ ရေးပါ

JSON format သာ return ပေးပါ (markdown မလိုပါ):
{{
  "title": "ဗီဒီယိုခေါင်းစဉ် (မြန်မာဘာသာ)",
  "source_title": "{video_title}",
  "source_url": "{youtube_url}",
  "hook": "ပထမ 10 စက္ကန့်အတွင်း viewer ဆွဲဆောင်မည့် ဝါကျ 2-3 ကြောင်း",
  "key_points": ["အဓိကအချက် 1", "အဓိကအချက် 2", "အဓိကအချက် 3"],
  "sections": [
    {{
      "heading": "အပိုင်းခေါင်းစဉ်",
      "content": "ဤအပိုင်း၏ အသေးစိတ်ရှင်းလင်းချက်",
      "duration_seconds": 60
    }}
  ],
  "outro": "နိဂုံးချုပ် + source credit + like/share တောင်းခံမည့် ဝါကျများ",
  "full_script": "အပိုင်း အားလုံးပေါင်းထားသော အပြည့်အစုံ script (hook မှ outro အထိ)",
  "thumbnail_text": "Thumbnail တွင်ဖော်ပြမည့် စာသား (မြန်မာ 5 လုံးအောက်)",
  "tags": ["tag1", "tag2", "tag3"]
}}"""

    print(f"🤖 OpenRouter API သို့ summarize/translate တောင်းဆိုနေသည်...")

    message = client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.choices[0].message.content.strip()

    # JSON parse
    try:
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        script_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        script_data = {
            "title": video_title or "YouTube Video Summary",
            "source_title": video_title,
            "source_url": youtube_url,
            "hook": f"ယနေ့ {video_title} အကြောင်း လေ့လာကြပါစို့",
            "key_points": [],
            "sections": [{"heading": "အဓိကအကြောင်းအရာ", "content": response_text, "duration_seconds": duration_minutes * 60}],
            "outro": "ကြည့်ရှုပေးသည့်အတွက် ကျေးဇူးတင်ပါသည်။ Like နှင့် Share လုပ်ပေးပါ။",
            "full_script": response_text,
            "thumbnail_text": (video_title or "Video")[:20],
            "tags": []
        }

    return script_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="YouTube video URL")
    parser.add_argument("--duration", type=int, default=3, help="Output duration in minutes")
    args = parser.parse_args()

    print(f"🎥 YouTube URL processing: {args.url}")

    # Extract video ID
    try:
        video_id = extract_youtube_id(args.url)
        print(f"  Video ID: {video_id}")
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Get metadata
    print("📋 Video metadata ထုတ်နေသည်...")
    metadata = get_video_metadata(video_id)
    if metadata.get('title'):
        print(f"  Title: {metadata['title']}")
        print(f"  Channel: {metadata.get('channel', 'N/A')}")
        print(f"  Duration: {metadata.get('duration', 0)//60}:{metadata.get('duration', 0)%60:02d}")

    # Get transcript
    print("📝 Transcript ထုတ်နေသည်...")
    transcript = get_transcript_via_api(video_id)

    if not transcript:
        print("  ⚠️ Transcript မရ၊ metadata မှ script ထုတ်မည်...")

    # Summarize & translate to Myanmar
    print(f"🌏 Myanmar script ပြောင်းနေသည် ({args.duration} မိနစ်)...")
    script_data = summarize_and_translate(
        transcript=transcript,
        metadata=metadata,
        youtube_url=args.url,
        duration_minutes=args.duration
    )

    # Save
    os.makedirs("output", exist_ok=True)

    with open("output/script_data.json", "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script_data.get("full_script", ""))

    # Save YouTube source info separately
    with open("output/source_info.json", "w", encoding="utf-8") as f:
        json.dump({
            "url": args.url,
            "video_id": video_id,
            "original_title": metadata.get('title', ''),
            "channel": metadata.get('channel', ''),
            "transcript_length": len(transcript),
            "had_transcript": bool(transcript)
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ Script ပြောင်းပြီး!")
    print(f"   Myanmar Title: {script_data.get('title', '')}")
    print(f"   Source: {metadata.get('title', args.url)}")
    print(f"   Sections: {len(script_data.get('sections', []))}")
    print(f"   Word count: {len(script_data.get('full_script', '').split())}")


if __name__ == "__main__":
    main()
  
