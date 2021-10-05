from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse

from .lib_twilio import send_sms, make_call

def index(request):
    return HttpResponse("Hello, world.")

# Endpoint for responding to incoming SMS messages to our Twilio number
@require_POST
@csrf_exempt # TODO: address CSRF if deploying to production
def sms_reply(request):
    incoming_msg = request.POST.get('Body', '').lower()

    # create Twilio response
    response = MessagingResponse()
    
    msg_body = ''
    media_link = ''

    if incoming_msg=='yo':
        msg_body = 'yo dawg'
    elif incoming_msg=='1':
        msg_body = 'Gotta love a GIF!'
        media_link= 'https://i.imgur.com/BwmtaWS.gif'
    elif incoming_msg=='2':
        msg_body='Enjoy this image!'
        media_link='https://i.imgur.com/zNxhPjp.jpeg'
    elif incoming_msg=='3':
        msg_body='Have a wonderful day'
    else:
        msg_body="""\nInvalid Option. \n\nWelcome to 1329 SVN! 🎉 \n\nReply with:\n1 to receive a GIF \n2 for an image \n3 for an SMS!"""

    msg = response.message(str(msg_body))
    if media_link:
        msg.media(media_link)
    
    return HttpResponse(response)

# Endpoint for responding to incoming calls to our Twilio number
@csrf_exempt # TODO: address CSRF if deploying to production
def call_answer(request):
    response = VoiceResponse()
    from_number = request.POST.get('From', '')

    if from_number == settings.TEST_NUMBER:
        response.say("Hey! This is a test. Have a wonderful day.")
    else:
        response.say('Hello, this is the SVN bot. Thank you for your call. Have a wonderful day!')
    
    return HttpResponse(str(response))

# Endpoint for sending SMS message from Twilio number
def test_sms(request):
    send_sms(settings.TEST_NUMBER, "hi! This is a test.")
    return HttpResponse('text sent')

# Endpoint for calling from Twilio number
def test_call(request):
    make_call(settings.TEST_NUMBER)
    return HttpResponse('call made')