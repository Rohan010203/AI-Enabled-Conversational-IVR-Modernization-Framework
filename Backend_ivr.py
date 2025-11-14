from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import time
import logging

app = FastAPI(title="AI-Enabled Conversational IVR Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------
#          SPEECH INTENT DETECTION LOGIC
# ---------------------------------------------------------------------

def detect_intent(speech: str):
    text = speech.lower()

    if "where is my train" in text or "train location" in text or "track my train" in text:
        return "train_location"
    if "book" in text and "ticket" in text:
        return "book"
    if "cancel" in text:
        return "cancel"
    if "refund" in text:
        return "refund"
    if "train" in text and "status" in text:
        return "train_status"
    if "seat" in text or "availability" in text:
        return "seat_availability"
    if "station" in text or "enquiry" in text:
        return "station_enquiry"

    return "unknown"


# ---------------------------------------------------------------------
#                     SPEECH IVR ENTRY
# ---------------------------------------------------------------------

@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_speech_entry():
    """Speech IVR entry point"""
    response = VoiceResponse()
    gather = Gather(input="speech", action="/ivr/handle-speech", method="POST", timeout=6)

    gather.say(
        "Welcome to the Indian Railway Smart Voice System. "
        "You can say things like: Where is my train, book a ticket, cancel ticket, "
        "refund status, train running status, seat availability, or station enquiry.",
        voice="alice"
    )

    response.append(gather)
    return Response(content=str(response), media_type="application/xml")


# ---------------------------------------------------------------------
#                   HANDLE SPEECH REQUEST
# ---------------------------------------------------------------------

@app.post("/ivr/handle-speech")
async def handle_speech(request: Request):
    """Handles Speech-to-Text commands from Twilio"""
    form = await request.form()
    speech_text = form.get("SpeechResult", "")

    logging.info(f"Speech recognized: {speech_text}")

    response = VoiceResponse()

    if not speech_text:
        response.say("Sorry, I did not hear anything. Please try again.", voice="alice")
        response.hangup()
        return Response(str(response), media_type="application/xml")

    intent = detect_intent(speech_text)

    # ---------------------------
    # NEW FEATURE: "Where is my train?"
    # ---------------------------
    if intent == "train_location":
        vr = VoiceResponse()
        gather = vr.gather(
            input="dtmf",
            num_digits=5,
            action="/ivr/train-location-result",
            method="POST"
        )
        gather.say("Sure. Please enter your 5 digit train number.", voice="alice")
        return Response(str(vr), media_type="application/xml")

    # Other intents
    intent_map = {
        "book": "Your ticket booking request has been initiated.",
        "cancel": "Your ticket cancellation request has been processed.",
        "refund": "Your refund is being processed.",
        "train_status": "The train is running on time.",
        "seat_availability": "Seats are available for your selected train.",
        "station_enquiry": "Please specify the station name next time."
    }

    message = intent_map.get(intent, "Sorry, I did not understand your request.")

    response.say(message, voice="alice")
    response.hangup()

    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------------------
#    TRAIN LOCATION — AFTER SPEECH USER ENTERS TRAIN NUMBER (DTMF)
# ---------------------------------------------------------------------

@app.post("/ivr/train-location-result")
async def train_location_result(request: Request):
    form = await request.form()
    train_no = form.get("Digits")

    vr = VoiceResponse()

    if train_no:
        vr.say(
            f"Your train number {train_no} is currently at Pune Junction.",
            voice="alice"
        )
        vr.say("Thank you for using the Indian Railway Smart Voice System.", voice="alice")
        vr.hangup()
    else:
        vr.say("No train number detected. Returning to main menu.", voice="alice")
        vr.redirect("/ivr")

    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------------------
# HEALTH + METRICS + TEST APIs
# ---------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "IVR backend is running fine."}


@app.get("/metrics")
async def metrics():
    uptime = round(time.process_time(), 2)
    return {
        "system": "AI-Enabled IVR",
        "uptime_seconds": uptime,
        "status": "operational"
    }


@app.api_route("/test/ivr", methods=["GET", "POST"])
async def test_ivr(request: Request):
    if request.method == "GET":
        return {"message": "POST: { 'input': 'where is my train' }"}

    data = await request.json()
    text = data.get("input", "")
    return {"input": text, "detected_intent": detect_intent(text)}


# ---------------------------------------------------------------------
# ROOT PAGE
# ---------------------------------------------------------------------

@app.get("/")
async def home():
    return {
        "message": "AI-Enabled Conversational IVR Modernization Framework 🚀",
        "status": "running",
        "endpoints": ["/ivr", "/health", "/metrics", "/test/ivr"]
    }
