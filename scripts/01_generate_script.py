#!/usr/bin/env python3
"""
Step 1: Gemini API သုံးပြီး Myanmar ဘာသာဖြင့် script ထုတ်မည်
"""

import argparse
import json
import os
import sys
import time
import google.generativeai as genai

def generate_script(topic: str, duration_minutes: int) -> dict:
    """Gemini API သုံးပြီး video script ထုတ်မည်"""
    
    words_per_minute = 120
    target_words = words_per_minute * duration_minutes
    
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    
    prompt = f"""သင်သည် မြန်မာဘာသာဖြင့် ဗီဒီယိုကြည့်ရှုသူများအတွက် engaging content ရေးသားသော expert တစ်ဦးဖြစ်သည်။

Topic: {topic}
Video Duration: {duration_minutes} မိနစ်
Target Word Count: {target_words} words (မြန်မာဘာသာ)

အောက်ပါ format ဖြင့် JSON သာ return ပေးပါ (markdown မလိုပါ):
{{
  "title": "ဗီဒီယိုခေါင်းစဉ်",
  "hook": "ပထမ 10 စက္ကန့်အတွင်း viewer ဆွဲဆောင်မည့် ဝါကျ 2-3 ကြောင်း",
  "sections": [
    {{
      "heading": "အပိုင်းခေါင်းစဉ်",
      "content": "ဤအပိုင်း၏ အသေးစိတ်ရှင်းလင်းချက် (speaker ပြောမည့်အတိုင်း သဘာဝကျကျ ရေးပါ)",
      "duration_seconds": 60
    }}
  ],
  "outro": "နိဂုံးချုပ် + like/share တောင်းခံမည့် ဝါကျများ",
  "full_script": "အပိုင်း အားလုံးပေါင်းထားသော အပြည့်အစုံ script (hook မှ outro အထိ)",
  "thumbnail_text": "Thumbnail တွင်ဖော်ပြမည့် စာသား (မြန်မာ 5 လုံးအောက်)",
  "tags": ["tag1", "tag2", "tag3"]
}}

ရေးသားရာတွင်:
- ပြောကြားသကဲ့သို့ သဘာဝကျကျ ရေးပါ
- ခက်ခဲသောဝေါဟာရများကို ရှင်းပြပါ  
- Engaging နှင့် informative ဖြစ်ပါစေ
- မြန်မာပြည်သူများ နားလည်လွယ်သော ဘာသာစကား သုံးပါ"""

    print(f"🤖 Gemini API သို့ script တောင်းဆိုနေသည်... (topic: {topic})")
    
    # Retry logic for rate limiting
    max_retries = 3
    retry_delays = [60, 90, 120]  # seconds

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=4096,
                )
            )
            response_text = response.text.strip()
            break  # success
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                if attempt < max_retries - 1:
                    wait = retry_delays[attempt]
                    print(f"⚠️ Rate limit ကျနေသည်။ {wait} စက္ကန့် စောင့်ပါမည်... (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait)
                else:
                    print(f"❌ Retry {max_retries} ကြိမ် မအောင်မြင်ပါ။")
                    raise
            else:
                raise

    # JSON parse
    try:
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        script_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        script_data = {
            "title": topic,
            "hook": f"{topic} အကြောင်း ယနေ့ လေ့လာကြပါစို့",
            "sections": [{"heading": "အဓိကအကြောင်းအရာ", "content": response_text, "duration_seconds": duration_minutes * 60}],
            "outro": "ကြည့်ရှုပေးသည့်အတွက် ကျေးဇူးတင်ပါသည်။ Like နှင့် Share လုပ်ပေးပါ။",
            "full_script": response_text,
            "thumbnail_text": topic[:20],
            "tags": [topic]
        }
    
    return script_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True, help="Video topic")
    parser.add_argument("--duration", type=int, default=3, help="Duration in minutes")
    args = parser.parse_args()
    
    print(f"📝 Script ထုတ်နေသည်: {args.topic} ({args.duration} မိနစ်)")
    
    script_data = generate_script(args.topic, args.duration)
    
    os.makedirs("output", exist_ok=True)
    
    with open("output/script_data.json", "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script_data.get("full_script", ""))
    
    print(f"✅ Script ထုတ်ပြီး!")
    print(f"   Title: {script_data.get('title', '')}")
    print(f"   Sections: {len(script_data.get('sections', []))}")
    print(f"   Word count: {len(script_data.get('full_script', '').split())}")


if __name__ == "__main__":
    main()
    
