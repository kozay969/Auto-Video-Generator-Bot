#!/usr/bin/env python3
import argparse
import json
import os
import sys
import google.generativeai as genai
from google.generativeai import types

def generate_script(topic: str, duration_minutes: int) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable is missing!")
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    
    words_per_minute = 120
    target_words = words_per_minute * duration_minutes
    
    prompt = f"""သင်သည် မြန်မာဘာသာဖြင့် ဗီဒီယိုကြည့်ရှုသူများအတွက် engaging content ရေးသားသော expert တစ်ဦးဖြစ်သည်။

Topic: {topic}
Video Duration: {duration_minutes} မိနစ်
Target Word Count: {target_words} words (မြန်မာဘာသာ)

အောက်ပါ format ဖြင့် JSON သာ return ပေးပါ (markdown ```json ... ``` မလိုပါ၊ pure JSON သာ ဖြစ်ရမည်):
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
}}"""

    print(f"🤖 Google Gemini API သို့ script တောင်းဆိုနေသည်... (topic: {topic})")
    
    # 💡 404 Beta Error ကို ကျော်လွှားရန် Stable API Version (v1) သုံးဖို့ အတင်းသတ်မှတ်ခြင်း
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )
        # API Client Options ကို သုံးပြီး API Version ကို v1 သို့ ပြောင်းလဲခြင်း
        response = model.generate_content(
            prompt,
            client_options={"api_version": "v1"}
        )
        response_text = response.text.strip()
    except Exception as api_error:
        print(f"❌ Gemini (v1) API Call Error: {api_error}")
        print("💡 နည်းလမ်းပြောင်းပြီး Beta API ဖြင့် 'models/gemini-1.5-flash' ကို ထပ်မံကြိုးစားကြည့်နေသည်...")
        try:
            model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
            response = model.generate_content(prompt)
            response_text = response.text.strip()
        except Exception as e_fallback:
            print(f"❌ Fallback Error: {e_fallback}")
            sys.exit(1)
    
    try:
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            if lines[0].startswith("```json"):
                response_text = "\n".join(lines[1:-1])
            else:
                response_text = "\n".join(lines[1:-1])
                
        script_data = json.loads(response_text)
    except Exception as e:
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
    
    script_data = generate_script(args.topic, args.duration)
    os.makedirs("output", exist_ok=True)
    with open("output/script_data.json", "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)
    with open("script.txt", "w", encoding="utf-8") as f:
        f.write(script_data.get("full_script", ""))
    print(f"✅ Gemini ဖြင့် Script ထုတ်ပြီး!")

if __name__ == "__main__":
    main()
    
