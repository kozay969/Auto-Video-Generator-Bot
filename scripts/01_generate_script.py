#!/usr/bin/env python3
import argparse
import json
import os
import sys
import google.generativeai as genai

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

အောက်ပါ format အတိုင်း JSON ပုံစံဖြင့်သာ ပြန်လည်ဖြေကြားပေးပါ:
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
    
    response_text = ""
    
    # ပြင်ဆင်ပြီး - 400/NameError များ အားလုံးကို ကျော်လွှားနိုင်ရန် ကုဒ်ကို စနစ်တကျ ပြန်လည်ဖွဲ့စည်းထားပါသည်
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        response_text = response.text.strip()
    except Exception as api_error:
        print(f"❌ Gemini (gemini-1.5-flash) Error: {api_error}")
        print("💡 နည်းလမ်းပြောင်းပြီး 'gemini-pro' ဖြင့် ထပ်မံကြိုးစားကြည့်နေသည်...")
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            response_text = response.text.strip()
        except Exception as e_fallback:
            print(f"❌ Fallback Error: {e_fallback}")
            sys.exit(1)
    
    # AI ပြန်ပေးတဲ့စာသားထဲက JSON ကို စနစ်တကျ ရှာဖွေဖတ်ယူခြင်း
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
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
    
