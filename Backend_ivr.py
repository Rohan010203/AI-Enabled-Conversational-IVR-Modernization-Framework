from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
import time

app = FastAPI(title="AI-Enabled Conversational IVR Modernization Framework")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)


# -------------------------
# VOICE CONFIG
# -------------------------
VOICES = {
    "en": ("alice", "en-IN"),     # Indian English voice
    "hi": ("Aditi", "hi-IN"),     # Indian Hindi voice
}


# ---------------------------------------------------------
# LANGUAGE SELECTION → MAIN ENTRY
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# STORE LANGUAGE AND GO TO MAIN MENU
# ---------------------------------------------------------
@app.post("/ivr/set-language")
async def set_language(request: Request):
    form = await request.form()
    choice = form.get("Digits")
    response = VoiceResponse()

    if choice == "1":
        response.say("You selected English.", voice="alice", language="en-IN")
        lang = "en"

    elif choice == "2":
        response.say("Aapne Hindi chuni hai.", voice="Aditi", language="hi-IN")
        lang = "hi"

    else:
        response.say("Invalid choice. Returning to main menu.", voice="alice", language="en-IN")
        response.redirect("/ivr")
        return Response(str(response), media_type="application/xml")

    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# MAIN MENU BASED ON LANGUAGE
# ---------------------------------------------------------
@app.get("/ivr/main-menu")
async def main_menu(lang: str):
    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    gather = Gather(
        input="speech",
        action=f"/ivr/handle-speech?lang={lang}",
        method="POST"
    )

    if lang == "en":
        gather.say(
            "Welcome to Indian Railway Smart Voice System. "
            "You can say: Where is my train, Ticket booking, Cancel ticket, Refund status, Seat availability.",
            voice=voice,
            language=lang_code
        )

    elif lang == "hi":
        gather.say(
            "Indian Railway Smart Voice System me aapka swagat hai. "
            "Bol sakte hain: Meri train kahan hai, Ticket book karo, Ticket cancel karo, Refund status, Seat availability.",
            voice=voice,
            language=lang_code
        )

    response.append(gather)
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# INTENT DETECTION
# ---------------------------------------------------------
def detect_intent(text: str):
    text = text.lower()

    if "where" in text or "train" in text or "kahan" in text:
        return "train_location"

    if "seat" in text or "availability" in text or "seat" in text:
        return "seat_availability"

    if "book" in text or "booking" in text or "ticket" in text:
        return "book_ticket"

    if "cancel" in text:
        return "cancel_ticket"

    if "refund" in text:
        return "refund_status"

    return "unknown"


# ---------------------------------------------------------
# HANDLE SPEECH → INTENT ROUTING
# ---------------------------------------------------------
@app.post("/ivr/handle-speech")
async def handle_speech(request: Request, lang: str):
    form = await request.form()
    speech = form.get("SpeechResult", "")
    intent = detect_intent(speech)

    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    # TRAIN LOCATION
    if intent == "train_location":
        gather = response.gather(
            input="dtmf",
            num_digits=5,
            action=f"/ivr/train-location?lang={lang}",
            method="POST"
        )
        if lang == "en":
            gather.say("Please enter your train number.", voice=voice, language=lang_code)
        else:
            gather.say("Kripya apna train number darj karein.", voice=voice, language=lang_code)

        return Response(str(response), media_type="application/xml")

    # SEAT AVAILABILITY
    if intent == "seat_availability":
        gather = response.gather(
            input="dtmf",
            num_digits=5,
            action=f"/ivr/seat-availability?lang={lang}",
            method="POST"
        )
        if lang == "en":
            gather.say("Enter your train number for seat availability.", voice=voice, language=lang_code)
        else:
            gather.say("Seat availability ke liye train number darj karein.", voice=voice, language=lang_code)

        return Response(str(response), media_type="application/xml")

    # UNKNOWN
    if lang == "en":
        response.say("Sorry, I did not understand.", voice=voice, language=lang_code)
    else:
        response.say("Maaf kijiye, main samajh nahi paaya.", voice=voice, language=lang_code)

    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# TRAIN LOCATION RESULT
# ---------------------------------------------------------
@app.post("/ivr/train-location")
async def train_location(request: Request, lang: str):
    form = await request.form()
    train_no = form.get("Digits")

    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    if lang == "en":
        response.say(f"Train {train_no} is currently at Pune Junction.", voice=voice, language=lang_code)
    else:
        response.say(f"Train {train_no} is samay Pune Junction par hai.", voice=voice, language=lang_code)

    response.hangup()
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
# SEAT AVAILABILITY RESULT
# ---------------------------------------------------------
@app.post("/ivr/seat-availability")
async def seat_availability(request: Request, lang: str):
    form = await request.form()
    train_no = form.get("Digits")

    response = VoiceResponse()
    voice, lang_code = VOICES[lang]

    if lang == "en":
        response.say(f"Seats are available for train number {train_no}.", voice=voice, language=lang_code)
    else:
        response.say(f"Train number {train_no} ke liye seats available hain.", voice=voice, language=lang_code)

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
