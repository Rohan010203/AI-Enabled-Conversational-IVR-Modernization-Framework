from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
import time
import logging

app = FastAPI()


## Milestone 2 ##

@app.api_route("/ivr", methods=["GET", "POST"])
async def ivr_entry():
    # Main IVR greeting and menu
    twiml = """
    <Response>
        <Say voice="alice">Hello, welcome to Indian Railway Booking System.</Say>
        <Say>
            Press 1 for Train Availability.
            Press 2 for PNR Status.
            Press 3 to talk to a Customer Agent.
            Press 4 for Ticket Cancellation.
            Press 5 for Refund Status.
            Press 6 for Train Running Status.
            Press 7 for Seat Availability.
            Press 8 for Station Enquiry.
            Press 9 to hear the Main Menu again.
        </Say>
        <Gather input="dtmf" timeout="5" numDigits="1" action="/ivr/handle-key" method="POST" />
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")


@app.post("/ivr/handle-key")
async def handle_key(request: Request):
    form = await request.form()
    digit_pressed = form.get("Digits")

    # Handle user keypress logic
    if digit_pressed == "1":
        msg = "You selected Train Availability. Please visit Indian Railways dot gov dot in for live schedules."
    elif digit_pressed == "2":
        msg = "You selected PNR Status. Please enter your ten digit PNR on the website or app."
    elif digit_pressed == "3":
        msg = "Connecting you to the nearest Railway customer agent. Please wait."
    elif digit_pressed == "4":
        msg = "You selected Ticket Cancellation. Please log in to your IRCTC account to cancel tickets."
    elif digit_pressed == "5":
        msg = "You selected Refund Status. Refunds are processed within seven working days."
    elif digit_pressed == "6":
        msg = "You selected Train Running Status. Please check live updates on Indian Railways dot gov dot in."
    elif digit_pressed == "7":
        msg = "You selected Seat Availability. Please check the availability chart on the IRCTC website."
    elif digit_pressed == "8":
        msg = "You selected Station Enquiry. Please contact the station help desk for more information."
    elif digit_pressed == "9":
        msg = "Returning to the Main Menu. Please listen carefully to the options again."
        # Loop back to main IVR menu
        twiml = """
        <Response>
            <Redirect>/ivr</Redirect>
        </Response>
        """
        return Response(content=twiml.strip(), media_type="application/xml")
    else:
        msg = "Invalid choice. Please press a number between 1 and 9 next time."

    # Generate the TwiML response
    twiml = f"""
    <Response>
        <Say voice="alice">{msg}</Say>
        <Hangup/>
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")

## Milestone 3 ##

def book_ticket():
    return "Your train ticket has been booked successfully."

def cancel_ticket():
    return "Your ticket has been cancelled successfully."

def check_refund():
    return "Your refund is being processed and will be credited soon."

def train_status():
    return "The train is running on time as per schedule."

def seat_availability():
    return "Seats are available for your selected route."

def station_enquiry():
    return "Please mention the station name for more information."

def unknown_intent():
    return "Sorry, I didn’t understand your request. Please try again."



def detect_intent(speech_text: str):
    text = speech_text.lower()

    if "book" in text and "ticket" in text:
        return "book"
    elif "cancel" in text:
        return "cancel"
    elif "refund" in text:
        return "refund"
    elif "train status" in text or "running" in text:
        return "train_status"
    elif "seat" in text or "availability" in text:
        return "seat_availability"
    elif "station" in text or "enquiry" in text:
        return "station_enquiry"
    else:
        return "unknown"



@app.api_route("/ivr/speech", methods=["GET", "POST"])
async def ivr_speech_entry():
    """Entry point for speech-based IVR"""
    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="/ivr/handle-speech",
        method="POST",
        timeout=6
    )

    gather.say(
        "Welcome to the Indian Railway Booking System. "
        "book a ticket, cancel my booking, check refund, "
        "train running status, seat availability, or station enquiry."
    )

    response.append(gather)
    return Response(content=str(response), media_type="application/xml")


@app.post("/ivr/handle-speech")
async def handle_speech(request: Request):
    """Handles natural language input"""
    form = await request.form()
    speech_text = form.get("SpeechResult")

    response = VoiceResponse()

    if speech_text:
        intent = detect_intent(speech_text)

        if intent == "book":
            message = book_ticket()
        elif intent == "cancel":
            message = cancel_ticket()
        elif intent == "refund":
            message = check_refund()
        elif intent == "train_status":
            message = train_status()
        elif intent == "seat_availability":
            message = seat_availability()
        elif intent == "station_enquiry":
            message = station_enquiry()
        else:
            message = unknown_intent()

        response.say(message, voice="alice")
    else:
        response.say("Sorry, I didn't hear you. Please try again.", voice="alice")

    response.hangup()
    return Response(content=str(response), media_type="application/xml")

# Milestone 4: Testing, Deployment & Monitoring


@app.get("/health")
async def health_check():
    """API Health Check Endpoint"""
    logging.info("Health check requested.")
    return JSONResponse({"status": "healthy", "message": "IVR backend is running fine."})

@app.get("/metrics")
async def metrics():
    """Simple performance and uptime monitoring"""
    uptime = round(time.process_time(), 2)
    logging.info("Metrics requested.")
    return JSONResponse({
        "system": "AI-Enabled IVR",
        "uptime_seconds": uptime,
        "status": "operational"
    })

@app.post("/test/ivr")
async def test_ivr_scenarios(request: Request):
    """Simulate testing scenarios for QA"""
    data = await request.json()
    test_input = data.get("input", "").lower()
    intent = detect_intent(test_input)
    logging.info(f"Testing scenario -> Input: {test_input}, Detected Intent: {intent}")
    return JSONResponse({"input": test_input, "detected_intent": intent})