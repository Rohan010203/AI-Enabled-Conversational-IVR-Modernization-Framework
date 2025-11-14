from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse

app = FastAPI()

@app.post("/ivr")
async def ivr_start(request: Request):
    response = VoiceResponse()

    gather = response.gather(
        input="speech",
        action="/process-voice",
        language="en-IN",
        speech_timeout="auto"
    )

    gather.say(
        "Namaste, this is the I R C T C conversational railway assistant. "
        "How can I help you today?",
        voice="alice"
    )

    return Response(content=str(response), media_type="application/xml")


# -----------------------------------------------------
# 2️⃣ Process Speech → Send to AI → Return Voice Output
# -----------------------------------------------------
@app.post("/process-voice")
async def process_voice(request: Request):
    form = await request.form()
    user_text = form.get("SpeechResult")

    response = VoiceResponse()

    if not user_text:
        response.say("Sorry, I did not catch that. Please say again.", voice="alice")
        response.redirect("/ivr")
        return Response(content=str(response), media_type="application/xml")

    # 🌟 AI PROCESSING
    ai_reply = get_ai_response(user_text)

    # 🌟 Return the AI Reply as Voice
    response.say(ai_reply, voice="alice")

    # Continue conversation
    response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")


# ------------------------------------------
# 3️⃣ AI Logic: Natural Conversation Handling
# ------------------------------------------
def get_ai_response(user_query):

    prompt = f"""
    You are an IRCTC Conversational Railway Assistant.
    Your job is to answer only train-related queries.

    User Query: {user_query}

    If user asks:
    - PNR status → ask for PNR
    - Train running status → ask train number
    - Ticket booking → ask destination, date, passenger details
    - Cancellation → ask PNR
    - Refund status → ask PNR
    - General questions → answer politely

    Keep replies short and simple for IVR.
    """

    completion = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    return completion.choices[0].message["content"]


# ✅ Step 4: Handle favicon (to avoid 404 logs)
@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)



