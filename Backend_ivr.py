from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
import time

app = FastAPI(title="AI Conversational IVR – English & Hindi (Speech Only)")

# ----------------- CORS -----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# ----------------- VOICES -----------------
VOICES = {
    "en": ("Polly.Joanna", "en-IN"),
    "hi": ("Polly.Aditi", "hi-IN"),
}

# ----------------- HOME / LANGUAGE SELECTION -----------------
@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_language():
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        speech_timeout="auto",
        action="/ivr/set-language",
        method="POST"
    )
    gather.say(
        "Please say your preferred language. Say English or Hindi.",
        voice="Polly.Joanna",
        language="en-IN"
    )
    response.append(gather)
    return Response(str(response), media_type="application/xml")

# ----------------- SET LANGUAGE -----------------
@app.post("/ivr/set-language")
async def set_language(request: Request):
    form = await request.form()
    speech = form.get("SpeechResult", "").lower()
    response = VoiceResponse()

    if "english" in speech:
        lang = "en"
        response.say("You selected English.", voice="Polly.Joanna", language="en-IN")
    elif "hindi" in speech or "hi" in speech:
        lang = "hi"
        response.say("Aapne Hindi chuni hai.", voice="Polly.Aditi", language="hi-IN")
    else:
        response.say("Sorry, I did not understand. Please try again.", voice="Polly.Joanna", language="en-IN")
        response.redirect("/ivr")
        return Response(str(response), media_type="application/xml")

    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")

# ----------------- MAIN MENU -----------------
@app.api_route("/ivr/main-menu", methods=["GET", "POST"])
async def main_menu(lang: str = "en"):
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    gather = Gather(
        input="speech",
        speech_timeout="auto",
        action=f"/ivr/handle-input?lang={lang}",
        method="POST"
    )

    if lang == "en":
        gather.say(
            "Welcome to Indian Railway Smart Voice System. "
            "You may say: Where is my train, Seat availability, Book ticket, Cancel ticket, Refund status.",
            voice=voice,
            language=lang_code
        )
    else:
        gather.say(
            "Indian Railway Smart Voice System mein aapka swagat hai. "
            "Aap bol sakte hain: Meri train kahan hai, Seat availability, Ticket book karo, Ticket cancel karo, Refund status.",
            voice=voice,
            language=lang_code
        )

    response.append(gather)
    return Response(str(response), media_type="application/xml")

# ----------------- INTENT DETECTION -----------------
def detect_intent(text: str):
    text = text.lower()
    if "where" in text or "train" in text or "kahan" in text:
        return "train_location"
    if "seat" in text or "availability" in text:
        return "seat_availability"
    if "book" in text or "booking" in text or "ticket" in text:
        return "book_ticket"
    if "cancel" in text:
        return "cancel_ticket"
    if "refund" in text:
        return "refund_status"
    return "unknown"

# ----------------- HANDLE SPEECH INPUT -----------------
@app.post("/ivr/handle-input")
async def handle_input(request: Request, lang: str = "en"):
    form = await request.form()
    speech = form.get("SpeechResult", "")
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    intent = detect_intent(speech)

    if intent in ["train_location", "seat_availability", "book_ticket", "cancel_ticket", "refund_status"]:
        gather = Gather(
            input="speech",
            speech_timeout="auto",
            action=f"/ivr/{intent}?lang={lang}",
            method="POST"
        )
        if lang == "en":
            gather.say(f"Please say your train number for {intent.replace('_',' ')}.", voice=voice, language=lang_code)
        else:
            gather.say(f"Kripya apna train number bolen for {intent.replace('_',' ')}.", voice=voice, language=lang_code)
        response.append(gather)
        return Response(str(response), media_type="application/xml")

    # Unknown input
    if lang == "en":
        response.say("Sorry, I did not understand.", voice=voice, language=lang_code)
    else:
        response.say("Maaf kijiye, main samajh nahi paaya.", voice=voice, language=lang_code)

    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")

# ----------------- INTENT HANDLERS -----------------
async def handle_train_no_response(request: Request, lang: str, message_template: str):
    form = await request.form()
    train_no = form.get("SpeechResult", "00000")
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]
    response.say(message_template.format(train_no=train_no), voice=voice, language=lang_code)
    response.hangup()
    return Response(str(response), media_type="application/xml")

@app.post("/ivr/train_location")
async def train_location(request: Request, lang: str = "en"):
    return await handle_train_no_response(
        request, lang,
        message_template="Train {train_no} is currently at Pune Junction." if lang=="en" else "Train {train_no} samay Pune Junction par hai."
    )

@app.post("/ivr/seat_availability")
async def seat_availability(request: Request, lang: str = "en"):
    return await handle_train_no_response(
        request, lang,
        message_template="Seats are available for train {train_no}." if lang=="en" else "Train {train_no} ke liye seats available hain."
    )

@app.post("/ivr/book_ticket")
async def book_ticket(request: Request, lang: str = "en"):
    return await handle_train_no_response(
        request, lang,
        message_template="Ticket booked for train {train_no}." if lang=="en" else "Train {train_no} ke liye ticket book ho gaya hai."
    )

@app.post("/ivr/cancel_ticket")
async def cancel_ticket(request: Request, lang: str = "en"):
    return await handle_train_no_response(
        request, lang,
        message_template="Ticket for train {train_no} has been cancelled." if lang=="en" else "Train {train_no} ke liye ticket cancel ho gaya hai."
    )

@app.post("/ivr/refund_status")
async def refund_status(request: Request, lang: str = "en"):
    return await handle_train_no_response(
        request, lang,
        message_template="Refund processed for train {train_no}." if lang=="en" else "Train {train_no} ke liye refund process ho gaya hai."
    )

# ----------------- HEALTH & METRICS -----------------
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return {"uptime_seconds": round(time.process_time(), 2)}

@app.get("/")
async def root():
    return {"message": "AI Enabled Conversational IVR (Speech Only, English + Hindi) 🚀"}
