from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
import time

app = FastAPI(title="AI Conversational IVR – Speech Only (Indian Voices)")

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
    "en": ("Polly.Raveena", "en-IN"),
    "hi": ("Polly.Aditi", "hi-IN"),
}

# ----------------- HOME / LANGUAGE SELECTION -----------------
@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_language():
    response = VoiceResponse()
    gather = Gather(input="speech", speech_timeout="auto", action="/ivr/set-language", method="POST")
    gather.say(
        "Welcome to Indian Railway Smart Voice System. "
        "Please say your preferred language. Say English for English or Hindi ke liye Hindi bole.",
        voice="Polly.Raveena", language="en-IN"
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
        response.say("You selected English.", voice="Polly.Raveena", language="en-IN")

    elif "hindi" in speech or "hi" in speech:
        lang = "hi"
        response.say("Aapne Hindi chuni hai.", voice="Polly.Aditi", language="hi-IN")

    else:
        response.say("Sorry, I did not understand. Please say English or Hindi.",
                     voice="Polly.Raveena", language="en-IN")
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
            "Please tell me how can I help you today. You can say: "
            "Where is my train, Seat availability, Book ticket, Cancel ticket, Refund status.",
            voice=voice, language=lang_code
        )
    else:
        gather.say(
            "Kripya bataye aaj main aapki kaise madad kar sakta hoon. "
            "Aap bol sakte hain: Meri train kahan hai, Seat availability, Ticket book karo, "
            "Ticket cancel karo, Refund status.",
            voice=voice, language=lang_code
        )

    response.append(gather)
    return Response(str(response), media_type="application/xml")

# ----------------- INTENT DETECTION -----------------
def detect_intent(text: str):
    text = (text or "").lower()
    if "where" in text or "kahan" in text or ("train" in text and "where" in text):
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
    voice, lang_code = VOICES.get(lang, VOICES["en"])

    intent = detect_intent(speech)

    if intent in ["train_location", "seat_availability", "book_ticket", "cancel_ticket", "refund_status"]:

        gather = Gather(
            input="speech",
            speech_timeout="auto",
            action=f"/ivr/{intent}?lang={lang}",
            method="POST"
        )

        # Ask for train number or PNR
        if intent in ["book_ticket", "seat_availability", "train_location"]:
            prompt_en = "Please say your train number."
            prompt_hi = "Kripya apna train number bataye."
        else:
            prompt_en = "Please say your PNR number."
            prompt_hi = "Kripya apna PNR number bataye."

        gather.say(prompt_en if lang == "en" else prompt_hi, voice=voice, language=lang_code)
        response.append(gather)
        return Response(str(response), media_type="application/xml")

    # If intent unknown
    error_msg = (
        "Sorry, I did not understand. Let's try again."
        if lang == "en"
        else "Maaf kijiye, main samaj nahi paaya. Dobara koshish karein."
    )
    response.say(error_msg, voice=voice, language=lang_code)
    response.redirect(f"/ivr/main-menu?lang={lang}")
    return Response(str(response), media_type="application/xml")

# --------------------------------------------------------------------
# ----------------------- INTENT HANDLERS -----------------------------
# --------------------------------------------------------------------

@app.post("/ivr/train_location")
async def train_location(request: Request, lang: str = "en"):
    form = await request.form()
    number = form.get("SpeechResult", "00000")
    response = VoiceResponse()
    voice, lang_code = VOICES.get(lang, VOICES["en"])

    if lang == "en":
        response.say(f"Train {number} is currently at Pune Junction.",
                     voice=voice, language=lang_code)
    else:
        response.say(f"Train {number} samay Pune Junction par hai.",
                     voice=voice, language=lang_code)

    if lang == "en":
        response.say("Thank you for using Indian Railway Smart Voice System. Goodbye!",
                     voice=voice, language=lang_code)
    else:
        response.say("Indian Railway Smart Voice System ka upyog karne ke liye dhanyavaad. Alvida!",
                     voice=voice, language=lang_code)

    response.hangup()
    return Response(str(response), media_type="application/xml")

# ----------------- SEAT AVAILABILITY -----------------
@app.post("/ivr/seat_availability")
async def seat_availability(request: Request, lang: str = "en"):
    form = await request.form()
    number = form.get("SpeechResult", "00000")
    response = VoiceResponse()
    voice, lang_code = VOICES.get(lang, VOICES["en"])

    if lang == "en":
        response.say(f"Seats are available for train {number}.",
                     voice=voice, language=lang_code)
    else:
        response.say(f"Train {number} ke liye seats available hain.",
                     voice=voice, language=lang_code)

    if lang == "en":
        response.say("Thank you for using Indian Railway Smart Voice System. Goodbye!",
                     voice=voice, language=lang_code)
    else:
        response.say("Indian Railway Smart Voice System ka upyog karne ke liye dhanyavaad. Alvida!",
                     voice=voice, language=lang_code)

    response.hangup()
    return Response(str(response), media_type="application/xml")

# ----------------- BOOK TICKET -----------------
@app.post("/ivr/book_ticket")
async def book_ticket(request: Request, lang: str = "en"):
    """
    This handler expects the user to say a train number (SpeechResult).
    After acknowledging booking, it notifies that PNR details are emailed.
    Note: If you later want a two-step flow (train -> PNR), we can add that.
    """
    form = await request.form()
    number = form.get("SpeechResult", "00000")  # treated as train number or PNR as per your choice
    response = VoiceResponse()
    voice, lang_code = VOICES.get(lang, VOICES["en"])

    if lang == "en":
        response.say(f"Ticket booked for train {number}.", voice=voice, language=lang_code)
        response.say(f"Detailed ticket information for PNR {number} has been sent to your registered email ID.",
                     voice=voice, language=lang_code)
    else:
        response.say(f"Train {number} ke liye ticket book ho gaya hai.", voice=voice, language=lang_code)
        response.say(f"PNR {number} ki vistaar se jaankari aapke registered email par bhej di gayi hai.",
                     voice=voice, language=lang_code)

    if lang == "en":
        response.say("Thank you for using Indian Railway Smart Voice System. Goodbye!",
                     voice=voice, language=lang_code)
    else:
        response.say("Indian Railway Smart Voice System ka upyog karne ke liye dhanyavaad. Alvida!",
                     voice=voice, language=lang_code)

    response.hangup()
    return Response(str(response), media_type="application/xml")

# ----------------- CANCEL TICKET -----------------
@app.post("/ivr/cancel_ticket")
async def cancel_ticket(request: Request, lang: str = "en"):
    form = await request.form()
    number = form.get("SpeechResult", "00000")  # PNR expected
    response = VoiceResponse()
    voice, lang_code = VOICES.get(lang, VOICES["en"])

    if lang == "en":
        response.say(f"Ticket for PNR {number} has been cancelled.", voice=voice, language=lang_code)
        response.say(f"Cancellation details for PNR {number} have been sent to your registered email ID.",
                     voice=voice, language=lang_code)
    else:
        response.say(f"PNR {number} ke liye ticket cancel ho gaya hai.", voice=voice, language=lang_code)
        response.say(f"PNR {number} ki cancel karne ki jaankari aapke registered email par bhej di gayi hai.",
                     voice=voice, language=lang_code)

    if lang == "en":
        response.say("Thank you for using Indian Railway Smart Voice System. Goodbye!",
                     voice=voice, language=lang_code)
    else:
        response.say("Indian Railway Smart Voice System ka upyog karne ke liye dhanyavaad. Alvida!",
                     voice=voice, language=lang_code)

    response.hangup()
    return Response(str(response), media_type="application/xml")

# ----------------- REFUND STATUS -----------------
@app.post("/ivr/refund_status")
async def refund_status(request: Request, lang: str = "en"):
    form = await request.form()
    number = form.get("SpeechResult", "00000")  # PNR expected
    response = VoiceResponse()
    voice, lang_code = VOICES.get(lang, VOICES["en"])

    if lang == "en":
        response.say(f"Refund has been processed for PNR {number}.", voice=voice, language=lang_code)
        response.say(f"Detailed refund information for PNR {number} has been emailed to your registered email ID.",
                     voice=voice, language=lang_code)
    else:
        response.say(f"PNR {number} ke liye refund process ho gaya hai.", voice=voice, language=lang_code)
        response.say(f"PNR {number} ki refund ki vistaar se jaankari aapke registered email par bhej di gayi hai.",
                     voice=voice, language=lang_code)

    if lang == "en":
        response.say("Thank you for using Indian Railway Smart Voice System. Goodbye!",
                     voice=voice, language=lang_code)
    else:
        response.say("Indian Railway Smart Voice System ka upyog karne ke liye dhanyavaad. Alvida!",
                     voice=voice, language=lang_code)

    response.hangup()
    return Response(str(response), media_type="application/xml")

# ----------------- HEALTH ENDPOINT -----------------
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return {"uptime_seconds": round(time.process_time(), 2)}

@app.get("/")
async def root():
    return {"message": "🚀 AI Enabled Conversational IVR is running successfully! Speak in English or Hindi to interact."}
