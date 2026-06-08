# 🎬 Auto Video Generator Bot

GitHub Actions + Claude AI + gTTS + Telegram ဖြင့် မြန်မာဘာသာ video အလိုအလျောက် ထုတ်သော bot

---

## 📋 Setup လုပ်နည်း (ဖုန်းဖြင့်)

### Step 1: Repository Fork/Clone

1. GitHub app ဖွင့်ပါ
2. ဤ repository ကို **Fork** လုပ်ပါ
3. သင်၏ account တွင် copy ဖြစ်မည်

---

### Step 2: Secrets 3 ခု ထည့်ရမည်

Repository **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

#### 🔑 Secret 1: `ANTHROPIC_API_KEY`
```
1. https://console.anthropic.com သွားပါ
2. API Keys → Create Key
3. Key ကို copy လုပ်ပါ
4. GitHub Secrets တွင် ANTHROPIC_API_KEY နာမည်ဖြင့် ထည့်ပါ
```

#### 🤖 Secret 2: `TELEGRAM_BOT_TOKEN`
```
1. Telegram တွင် @BotFather ကို message ပို့ပါ
2. /newbot လုပ်ပါ
3. Bot နာမည်ပေးပါ
4. Token ကို copy → GitHub Secret တွင် ထည့်ပါ
```

#### 💬 Secret 3: `TELEGRAM_CHAT_ID`
```
1. Bot ကို start လုပ်ပါ (သင့် bot ကို message တစ်ခု ပို့ပါ)
2. Browser တွင် ဤ URL သွားပါ:
   https://api.telegram.org/bot{YOUR_TOKEN}/getUpdates
3. "chat":{"id": xxxxxxxxx} ကို ရှာပါ
4. ထို number ကို TELEGRAM_CHAT_ID ဖြင့် ထည့်ပါ
```

---

### Step 3: Video ထုတ်နည်း

1. GitHub Repository ဖွင့်ပါ
2. **Actions** tab ကို နှိပ်ပါ
3. **🎬 Auto Video Generator** ကို ရွေးပါ
4. **Run workflow** ကို နှိပ်ပါ
5. Topic ရိုက်ထည့်ပါ (ဥပမာ: "Python programming ကို မြန်မာဘာသာဖြင့် မိတ်ဆက်ခြင်း")
6. Duration ရွေးပါ (2/3/5 မိနစ်)
7. **Run workflow** ကို နှိပ်ပါ

ခဏစောင့်ပါ (~10-15 မိနစ်) → Telegram တွင် video ရောက်မည်!

---

## ⏱️ Processing Time

| Step | ကြာချိန် |
|------|---------|
| Script Generate | ~30 seconds |
| TTS (gTTS) | ~1-2 minutes |
| Video Render | ~5-10 minutes |
| Telegram Upload | ~1-3 minutes |
| **Total** | **~10-15 minutes** |

---

## 💰 Free Limits

| Service | Free Limit |
|---------|-----------|
| GitHub Actions | 2,000 min/month (~100 videos) |
| Anthropic API | $5 credit (~500 videos) |
| gTTS | Unlimited ✅ |
| Telegram Bot | Unlimited ✅ |

---

## 🔧 Troubleshooting

**Video မရောက်ရင်:**
- Actions log ကြည့်ပါ (red X ကို နှိပ်)
- Secrets မှန်မမှန် စစ်ပါ
- Artifacts section တွင် video download လုပ်နိုင်သည်

**gTTS Myanmar မအလုပ်လုပ်ရင်:**
- Internet connection စစ်ပါ
- English fallback အလိုအလျောက် သုံးမည်

---

## 📁 File Structure

```
.
├── .github/
│   └── workflows/
│       └── generate-video.yml    ← Main workflow
├── scripts/
│   ├── 01_generate_script.py     ← Claude API → Script
│   ├── 02_text_to_speech.py      ← gTTS → Audio
│   ├── 03_create_video.py        ← FFmpeg → Video
│   └── 04_send_telegram.py       ← Telegram → Send
└── README.md
```
