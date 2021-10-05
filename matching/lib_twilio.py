from django.conf import settings
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

# Set up Twilio client
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def send_sms(to_number, body):
    try:
        message = client.messages.create(
            to=to_number,
            from_=settings.TWILIO_NUMBER,
            body=body)
        print("SID of message sent: " + message.sid)
        return message.sid
    except TwilioRestException as e:
        # Implement fallback code
        print("Failed to send SMS with following exception: " + e)

def make_call(to_number, url = None):
    if url is None:
        url="http://demo.twilio.com/docs/voice.xml"
    
    call = client.calls.create(
        to=to_number,
        from_=settings.TWILIO_NUMBER,
        url=url
    )

    print("SID of call made: " + call.sid)
    return call.sid
