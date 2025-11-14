from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging

app = FastAPI(title="AI Conversational IVR – English & Hindi")

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
    "en": ("alice", "en-IN"),   # Indian English
    "hi": ("Aditi", "hi-IN"),   # Indian Hindi
}

# ----------------- HOME / LANGUAGE SELECTION -----------------
@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_language():
    response = VoiceResponse()
    gather = Gather(
        input="dtmf",
        num_digits=1,
        action="/ivr/set-language",
        method="POST"
    )
    gather.say(
        "Press 1 for English. Hindi ke liye 2 dabaye.",
        voice="alice",
        language="en-IN"
    )
    response.append(gather)
    return Response(str(response), media_type="application/xml")

# ----------------- SET LANGUAGE & REDIRECT TO MAIN MENU -----------------
@app.post("/ivr/set-language")
async def set_language(request: Request):
    form = await request.form()
    choice = form.get("Digits", "")
    response = VoiceResponse()

    if choice == "1":
        lang = "en"
        response.say("You selected English.", voice="alice", language="en-IN")
    elif choice == "2":
        lang = "hi"
        response.say("Aapne Hindi chuni hai.", voice="Aditi", language="hi-IN")
    else:
        response.say("Invalid choice. Please try again.", voice="alice", language="en-IN")
        response.redirect("/ivr")
        return Response(str(response), media_type="application/xml")

    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")

# ----------------- MAIN MENU (SPEECH + OPTIONS) -----------------
@app.api_route("/ivr/main-menu", methods=["GET", "POST"])
async def main_menu(lang: str = "en"):
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    gather = Gather(
        input="speech dtmf",
        num_digits=1,
        action=f"/ivr/handle-input?lang={lang}",
        method="POST"
    )

    if lang == "en":
        gather.say(
            "Welcome to Indian Railway Smart Voice System. "
            "You may say: Where is my train, Seat availability, Book ticket, Cancel ticket, Refund status. "
            "Or press 1 for Train Location, 2 for Seat Availability, 3 for Book Ticket, 4 for Cancel Ticket, 5 for Refund Status.",
            voice=voice,
            language=lang_code
        )
    else:
        gather.say(
            "Indian Railway Smart Voice System mein aapka swagat hai. "
            "Aap bol sakte hain: Meri train kahan hai, Seat availability, Ticket book karo, Ticket cancel karo, Refund status. "
            "Ya press karein 1 Train Location, 2 Seat Availability, 3 Ticket Booking, 4 Ticket Cancel, 5 Refund Status.",
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

# ----------------- HANDLE SPEECH OR DTMF INPUT -----------------
@app.post("/ivr/handle-input")
async def handle_input(request: Request, lang: str = "en"):
    form = await request.form()
    dtmf = form.get("Digits")
    speech = form.get("SpeechResult", "")
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    # DTMF Mapping
    if dtmf:
        mapping = {
            "1": "train_location",
            "2": "seat_availability",
            "3": "book_ticket",
            "4": "cancel_ticket",
            "5": "refund_status"
        }
        intent = mapping.get(dtmf, "unknown")
    else:
        intent = detect_intent(speech)

    # REDIRECT TO INTENT HANDLERS
    if intent in ["train_location", "seat_availability", "book_ticket", "cancel_ticket", "refund_status"]:
        gather = response.gather(
            input="dtmf",
            num_digits=5,
            action=f"/ivr/{intent}?lang={lang}",
            method="POST"
        )
        if lang == "en":
            gather.say(f"Please enter your train number for {intent.replace('_',' ')}.", voice=voice, language=lang_code)
        else:
            gather.say(f"Kripya apna train number darj karein for {intent.replace('_',' ')}.", voice=voice, language=lang_code)
        return Response(str(response), media_type="application/xml")

    # UNKNOWN
    if lang == "en":
        response.say("Sorry, I did not understand.", voice=voice, language=lang_code)
    else:
        response.say("Maaf kijiye, main samajh nahi paaya.", voice=voice, language=lang_code)

    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")

# ----------------- INTENT HANDLERS -----------------
@app.post("/ivr/train_location")
async def train_location(request: Request, lang: str = "en"):
    form = await request.form()
    train_no = form.get("Digits", "00000")
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    if lang == "en":
        response.say(f"Train {train_no} is currently at Pune Junction.", voice=voice, language=lang_code)
    else:
        response.say(f"Train {train_no} samay Pune Junction par hai.", voice=voice, language=lang_code)
    response.hangup()
    return Response(str(response), media_type="application/xml")

@app.post("/ivr/seat_availability")
async def seat_availability(request: Request, lang: str = "en"):
    form = await request.form()
    train_no = form.get("Digits", "00000")
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    if lang == "en":
        response.say(f"Seats are available for train {train_no}.", voice=voice, language=lang_code)
    else:
        response.say(f"Train {train_no} ke liye seats available hain.", voice=voice, language=lang_code)
    response.hangup()
    return Response(str(response), media_type="application/xml")

@app.post("/ivr/book_ticket")
async def book_ticket(request: Request, lang: str = "en"):
    form = await request.form()
    train_no = form.get("Digits", "00000")
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    if lang == "en":
        response.say(f"Ticket booked for train {train_no}.", voice=voice, language=lang_code)
    else:
        response.say(f"Train {train_no} ke liye ticket book ho gaya hai.", voice=voice, language=lang_code)
    response.hangup()
    return Response(str(response), media_type="application/xml")

@app.post("/ivr/cancel_ticket")
async def cancel_ticket(request: Request, lang: str = "en"):
    form = await request.form()
    train_no = form.get("Digits", "00000")
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    if lang == "en":
        response.say(f"Ticket for train {train_no} has been cancelled.", voice=voice, language=lang_code)
    else:
        response.say(f"Train {train_no} ke liye ticket cancel ho gaya hai.", voice=voice, language=lang_code)
    response.hangup()
    return Response(str(response), media_type="application/xml")

@app.post("/ivr/refund_status")
async def refund_status(request: Request, lang: str = "en"):
    form = await request.form()
    train_no = form.get("Digits", "00000")
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    if lang == "en":
        response.say(f"Refund processed for train {train_no}.", voice=voice, language=lang_code)
    else:
        response.say(f"Train {train_no} ke liye refund process ho gaya hai.", voice=voice, language=lang_code)
    response.hangup()
    return Response(str(response), media_type="application/xml")

# ---------------------------------------------------------
# HEALTH + METRICS
# ---------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return {"uptime_seconds": round(time.process_time(), 2)}

@app.get("/")
async def root():
    return {"message": "AI Enabled Conversational IVR (English + Hindi + Indian Voices) 🚀"}

