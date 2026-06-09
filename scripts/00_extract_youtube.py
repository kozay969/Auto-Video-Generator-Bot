#!/usr/bin/env python3
"""
Step 0: YouTube Video မှ Transcript/Captions ထုတ်ပြီး Myanmar script အတွက် summarize မည်
"""

import argparse
import json
import os
import re
import sys
import time
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

        # Auto-generated fallback - try ALL available transcripts
        if not transcript:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                all_transcripts = list(transcript_list)
                if all_transcripts:
                    # Prefer non-auto-generated first
                    manual = [t for t in all_transcripts if not t.is_generated]
                    auto = [t for t in all_transcripts if t.is_generated]
                    chosen = (manual or auto)[0]
                    transcript = chosen.fetch()
                    used_lang = chosen.language_code
                    print(f"  ✅ Auto transcript ရပြီ ({used_lang})")
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
    except Exception as e:
        print(f"  ⚠️ Transcript unexpected error: {e}")
        return ""


def get_video_metadata(video_id: str, retries: int = 3) -> dict:
    """yt-dlp သုံးပြီး video metadata ထုတ်မည် (retry + bot-detection bypass)"""
    import subprocess

    base_cmd = [
        'yt-dlp',
        '--dump-json',
        '--no-playlist',
        '--skip-download',
        '--no-warnings',
        # Browser impersonation to bypass bot detection
        '--user-agent',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        '--add-header', 'Accept-Language:en-US,en;q=0.9',
        '--extractor-args', 'youtube:player_client=web',
        f'https://www.youtube.com/watch?v={video_id}'
    ]

    for attempt in range(1, retries + 1):
        try:
            print(f"  🔄 Metadata attempt {attempt}/{retries}...")
            result = subprocess.run(
                base_cmd,
                capture_output=True,
                text=True,
                timeout=90
            )

            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                meta = {
                    'title': data.get('title', ''),
                    'description': data.get('description', '')[:1000],
                    'duration': data.get('duration', 0),
                    'channel': data.get('uploader', ''),
                    'view_count': data.get('view_count', 0),
                    'tags': data.get('tags', [])[:10],
                }
                print(f"  ✅ Metadata ရပြီ: {meta['title'][:60]}")
                return meta
            else:
                err = result.stderr.strip()[:200] if result.stderr else "no output"
                print(f"  ⚠️ yt-dlp attempt {attempt} failed: {err}")

        except subprocess.TimeoutExpired:
            print(f"  ⚠️ yt-dlp attempt {attempt} timed out")
        except Exception as e:
            print(f"  ⚠️ Metadata error attempt {attempt}: {e}")

        if attempt < retries:
            time.sleep(3 * attempt)  # exponential backoff

    print("  ❌ All metadata attempts failed — continuing with empty metadata")
    return {'title': '', 'description': '', 'duration': 0, 'channel': '', 'tags': []}


def build_context_from_url(youtube_url: str, video_id: str) -> str:
    """Transcript/metadata မရရင် URL မှ basic context ဆောက်မည်"""
    return f"YouTube Video ID: {video_id}\nSource URL: {youtube_url}"


def summarize_and_translate(
    transcript: str,
    metadata: dict,
    youtube_url: str,
    duration_minutes: int,
    video_id: str = ""
) -> dict:
    """OpenRouter API သုံးပြီး transcript ကို Myanmar script အဖြစ် ပြန်ဆိုပြီး summarize မည်"""

    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1"
    )

    words_per_minute = 120
    target_words = words_per_minute * duration_minutes

    video_title = metadata.get('title', '')
    description = metadata.get('description', '')
    channel = metadata.get('channel', '')

    # Build context — graceful fallback if everything is empty
    context_parts = []
    if video_title:
        context_parts.append(f"Video Title: {video_title}")
    if channel:
        context_parts.append(f"Channel: {channel}")
    if description:
        context_parts.append(f"Description: {description[:500]}")
    if transcript:
        context_parts.append(f"Transcript:\n{transcript[:6000]}")

    # ── FALLBACK: if nothing worked, use URL/ID as minimal context ──
    if not context_parts:
        print("  ⚠️ Transcript/metadata မရပါ — URL မှ script ထုတ်မည်")
        fallback_ctx = build_context_from_url(youtube_url, video_id)
        context_parts.append(fallback_ctx)
        # Let LLM know it has no source material
        context_parts.append(
            "Note: No transcript or metadata was available for this video. "
            "Please generate a creative and informative Myanmar script based on "
            "what can be inferred from the URL/ID, and make it engaging for viewers."
        )
        video_title = video_title or f"YouTube Video ({video_id})"

    context = "\n\n".join(context_parts)

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

    # JSON parse — strip markdown fences if present
    try:
        # Handle ```json ... ``` or ``` ... ```
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first and last fence lines
            inner = lines[1:] if lines[-1].strip() == "```" else lines[1:]
            if inner and inner[-1].strip() == "```":
                inner = inner[:-1]
            response_text = "\n".join(inner)

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

    # Get metadata (with retry + bot-bypass)
    print("📋 Video metadata ထုတ်နေသည်...")
    metadata = get_video_metadata(video_id)
    if metadata.get('title'):
        print(f"  Title: {metadata['title']}")
        print(f"  Channel: {metadata.get('channel', 'N/A')}")
        dur = metadata.get('duration', 0)
        print(f"  Duration: {dur//60}:{dur%60:02d}")

    # Get transcript
    print("📝 Transcript ထုတ်နေသည်...")
    transcript = get_transcript_via_api(video_id)

    if not transcript:
        print("  ⚠️ Transcript မရ — metadata မှ script ဆက်ထုတ်မည်")

    # Summarize & translate
    print(f"🌏 Myanmar script ပြောင်းနေသည် ({args.duration} မိနစ်)...")
    script_data = summarize_and_translate(
        transcript=transcript,
        metadata=metadata,
        youtube_url=args.url,
        duration_minutes=args.duration,
        video_id=video_id
    )

    # Save outputs
    os.makedirs("output", exist_ok=True)

    with open("output/script_data.json", "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script_data.get("full_script", ""))

    with open("output/source_info.json", "w", encoding="utf-8") as f:
        json.dump({
            "url": args.url,
            "video_id": video_id,
            "original_title": metadata.get('title', ''),
            "channel": metadata.get('channel', ''),
            "transcript_length": len(transcript),
            "had_transcript": bool(transcript),
            "had_metadata": bool(metadata.get('title'))
        }, f, ensure_ascii=False, indent=2)

    print(f"✅ Script ပြောင်းပြီး!")
    print(f"   Myanmar Title: {script_data.get('title', '')}")
    print(f"   Source: {metadata.get('title', args.url)}")
    print(f"   Sections: {len(script_data.get('sections', []))}")
    print(f"   Word count: {len(script_data.get('full_script', '').split())}")


if __name__ == "__main__":
    main()
    
