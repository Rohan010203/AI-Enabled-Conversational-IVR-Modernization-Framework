from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse, Gather
import time
import logging

app = FastAPI(title="AI-Enabled Conversational IVR Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------
#                  INTENT DETECTION
# ---------------------------------------------------------
def detect_intent(speech: str):
    text = speech.lower()

    # Main smart IVR flows
    if "where is my train" in text or "train location" in text or "track my train" in text:
        return "train_location"

    if "book ticket" in text or "book a ticket" in text:
        return "book_ticket_flow"

    if "cancel ticket" in text or "cancel my booking" in text:
        return "cancel_ticket_flow"

    if "refund" in text or "refund status" in text:
        return "refund_status_flow"

    # Additional simple intents
    if "train status" in text:
        return "train_status"

    if "seat availability" in text:
        return "seat_availability"

    if "station enquiry" in text or "station info" in text:
        return "station_enquiry"

    return "unknown"


# ---------------------------------------------------------
#                  SPEECH IVR ENTRY POINT
# ---------------------------------------------------------
@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_entry():
    response = VoiceResponse()
    gather = Gather(input="speech", action="/ivr/handle-speech", method="POST", timeout=6)
    gather.say(
        "Welcome to the Indian Railway System. "
        "You can say: where is my train, book ticket, cancel ticket, refund status, "
        "train status, seat availability, or station enquiry.",
        voice="alice"
    )
    response.append(gather)
    return Response(str(response), media_type="application/xml")


# ---------------------------------------------------------
#             HANDLE SPEECH RECOGNITION OUTPUT
# ---------------------------------------------------------
@app.post("/ivr/handle-speech")
async def handle_speech(request: Request):
    form = await request.form()
    speech_text = form.get("SpeechResult", "")

    logging.info(f"Speech recognized: {speech_text}")

    if not speech_text:
        vr = VoiceResponse()
        vr.say("Sorry, I did not hear anything. Please try again.", voice="alice")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    intent = detect_intent(speech_text)

    # -----------------------------------------
    # Smart conversational flow 1: Train Location
    # -----------------------------------------
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

    # -----------------------------------------
    # Smart flow 2: Book Ticket
    # -----------------------------------------
    if intent == "book_ticket_flow":
        vr = VoiceResponse()
        gather = vr.gather(
            input="dtmf",
            num_digits=5,
            action="/ivr/book-ticket",
            method="POST"
        )
        gather.say("To book your ticket, please enter your 5 digit train number.", voice="alice")
        return Response(str(vr), media_type="application/xml")

    # -----------------------------------------
    # Smart flow 3: Cancel Ticket
    # -----------------------------------------
    if intent == "cancel_ticket_flow":
        vr = VoiceResponse()
        gather = vr.gather(
            input="dtmf",
            num_digits=10,
            action="/ivr/cancel-ticket",
            method="POST"
        )
        gather.say("Please enter your 10 digit P N R number to cancel your ticket.", voice="alice")
        return Response(str(vr), media_type="application/xml")

    # -----------------------------------------
    # Smart flow 4: Refund Status
    # -----------------------------------------
    if intent == "refund_status_flow":
        vr = VoiceResponse()
        gather = vr.gather(
            input="dtmf",
            num_digits=10,
            action="/ivr/refund-status",
            method="POST"
        )
        gather.say("Please enter your 10 digit P N R number to check your refund status.", voice="alice")
        return Response(str(vr), media_type="application/xml")

    # ---------------------------
    # Simple direct intents
    # ---------------------------
    direct_intents = {
        "train_status": "The train is running on time.",
        "seat_availability": "Seats are available for your selected train.",
        "station_enquiry": "Please specify the station name next time."
    }

    message = direct_intents.get(intent, "Sorry, I did not understand your request.")

    vr = VoiceResponse()
    vr.say(message, voice="alice")
    vr.hangup()
    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#        TRAIN LOCATION — USER ENTERS TRAIN NUMBER
# ---------------------------------------------------------
@app.post("/ivr/train-location-result")
async def train_location_result(request: Request):
    form = await request.form()
    train_no = form.get("Digits")

    vr = VoiceResponse()
    if train_no:
        vr.say(f"Your train number {train_no} is currently at Pune Junction.", voice="alice")
        vr.say("Thank you for using the Indian Railway Smart Voice System.", voice="alice")
        vr.hangup()
    else:
        vr.say("Invalid train number. Returning to main menu.", voice="alice")
        vr.redirect("/ivr")
    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#        BOOK TICKET — USER ENTERS TRAIN NUMBER
# ---------------------------------------------------------
@app.post("/ivr/book-ticket")
async def book_ticket_result(request: Request):
    form = await request.form()
    train_no = form.get("Digits")

    vr = VoiceResponse()
    if train_no:
        vr.say(f"Your ticket for train number {train_no} has been booked successfully.", voice="alice")
        vr.hangup()
    else:
        vr.say("Invalid number. Redirecting to main menu.", voice="alice")
        vr.redirect("/ivr")
    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#      CANCEL TICKET — USER ENTERS PNR NUMBER
# ---------------------------------------------------------
@app.post("/ivr/cancel-ticket")
async def cancel_ticket_result(request: Request):
    form = await request.form()
    pnr = form.get("Digits")

    vr = VoiceResponse()
    if pnr:
        vr.say(f"Your ticket with P N R number {pnr} has been cancelled successfully.", voice="alice")
        vr.hangup()
    else:
        vr.say("Invalid P N R. Returning to main menu.", voice="alice")
        vr.redirect("/ivr")
    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
#       REFUND STATUS — USER ENTERS PNR NUMBER
# ---------------------------------------------------------
@app.post("/ivr/refund-status")
async def refund_status_result(request: Request):
    form = await request.form()
    pnr = form.get("Digits")

    vr = VoiceResponse()
    if pnr:
        vr.say(f"The refund for P N R number {pnr} is being processed and will be credited soon.", voice="alice")
        vr.hangup()
    else:
        vr.say("Invalid P N R. Returning to main menu.", voice="alice")
        vr.redirect("/ivr")
    return Response(str(vr), media_type="application/xml")


# ---------------------------------------------------------
# HEALTH + METRICS + TEST
# ---------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "AI IVR running"}

@app.get("/metrics")
async def metrics():
    return {"uptime_seconds": round(time.process_time(), 2)}

@app.api_route("/test/ivr", methods=["GET", "POST"])
async def test_ivr(request: Request):
    if request.method == "GET":
        return {"message": "POST {input: 'where is my train'} to test"}
    data = await request.json()
    text = data.get("input", "")
    return {"input": text, "intent": detect_intent(text)}


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "AI-Enabled Conversational IVR Modernization Framework 🚀",
        "routes": ["/ivr", "/health", "/metrics", "/test/ivr"]
    }

