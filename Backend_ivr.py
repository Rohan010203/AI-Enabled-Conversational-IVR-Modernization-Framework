from fastapi import FastAPI, Request
from fastapi.responses import Response

app = FastAPI()

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
