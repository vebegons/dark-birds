import os
import assemblyai as aai
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from deep_translator import GoogleTranslator
import yt_dlp

# --- الإعدادات الأساسية ---
aai.settings.api_key = "3c44007830ef4c3397cfb96cbbe8f3c6" # مفتاح AssemblyAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- تحميل الواجهة الأمامية ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

# --- نقطة نهاية لتحليل الفيديو من رابط ---
@app.post("/api/process_url")
async def process_url(url: str = Form(...)):
    try:
        ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            if not audio_url:
                raise HTTPException(status_code=400, detail="لم يتم العثور على رابط صوت مباشر.")
            
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(audio_url, config=aai.TranscriptionConfig(language_detection=True))

            if transcript.status == aai.TranscriptStatus.error:
                raise HTTPException(status_code=500, detail=transcript.error)

            return {"text": transcript.text, "language_code": transcript.language_code}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حدث خطأ: {str(e)}")

# --- نقطة نهاية لتحليل ملف مرفوع ---
@app.post("/api/process_file")
async def process_file(file: UploadFile = File(...)):
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(file.file, config=aai.TranscriptionConfig(language_detection=True))

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=transcript.error)

        return {"text": transcript.text, "language_code": transcript.language_code}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"حدث خطأ: {str(e)}")

# --- نقطة نهاية للترجمة ---
@app.post("/api/translate")
async def translate_text(text: str = Form(...), target_lang: str = Form(...)):
    try:
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return {"translated_text": translated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في الترجمة: {str(e)}")
