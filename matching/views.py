import json
import random

from django.http import HttpResponse
from django.http import Http404
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse

from matching.models import CustomUser

from .lib_twilio import send_sms, make_call

num_matches = 3

def index(request):
    return HttpResponse("Hello, world.")

@csrf_exempt # TODO: address CSRF if deploying to production
def match_users(request):

    # Only attempt to match users that haven't been matched yet.
    users_not_matched = CustomUser.objects.filter(match_ids__len=0)

    total_count = CustomUser.objects.count()

    for user in users_not_matched:
        # Generate 3 random matches (1 to N, where N is total) and save to DB
        # TODO: refine this. Right now this biases towards "overmatching" on
        # those who show up a little bit earlier because their user IDs will be available
        # for selection in this process potentialy more than once.
        matches = []
        while len(matches) != 3:
            match = random.randint(1, total_count)
            if match == user.id:
                # Exclude invalid self-matches.
                continue
            matches.append(match)

        user.match_ids = matches
        user.save()

        # Find fun facts about matches and send text notifying about matches
        fun_facts = []
        for match_id in user.match_ids:
            fun_facts.append(CustomUser.objects.get(pk=match_id).fun_fact)
        send_matches(user, fun_facts)

    return HttpResponse(f"matched all users!")

def send_matches(user, fun_facts):

    match_msg = f'''
Here are the fun facts about your {num_matches} matches...
    
    '''
    for i, fact in enumerate(fun_facts):
        match_msg += "\n" + f"{i+1}. {fact}"

    match_msg += "\n\nText us their names when you think you've found them!"

    # send_sms(user.phone_num, match_msg)

    print(match_msg)

    return

#@require_POST
@csrf_exempt # TODO: address CSRF if deploying to production
def add_user(request):

    # Parse request -> extract name, phone number, and fun fact
    print(request.POST)
    body = request.__dict__['environ']['wsgi.input'].read()

    print(body)

    params = json.loads(body)

    print(params)

    user_id = params['user_id']
    first_name = params['first_name']
    last_name = params['last_name']
    phone_num = params['phone_number']
    fun_fact = params['fun_fact']

    # Create new user in DB
    # TODO: add validation to ensure no duplicate numbers
    user = CustomUser(phone = phone_num, first_name = first_name, last_name = last_name, fun_fact = fun_fact)
    user.save()

    # Find 3 random users -> lock them in as matches
    # rows = db_query(USERS)
    # for i < 3: matches.append(randint(1, len(rows))) # excluding myself

    # send greeting text
    greeting_msg = f'''
    Hey {first_name}! Welcome to 1329 SVN 🎉
    
Tonight we will be playing a little game — in a few moments you will receive 3 fun facts about others at this party.

These are your matches for the night, and your job is to find them. Once you think you've found them, text us their name and we will try confirm if it's the right person!

Fastest person to find all 3 matches wins a secret prize 🤫
    '''
    # Use actual number from form
    send_sms(phone_num, greeting_msg)

    # if MATCH_PUBLISH (turned on after a certain time), send matches

    return HttpResponse(json.dumps({"message":f"user {first_name} added with user_id: {user.id}"}))


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
        msg_body="""\n\n\nWelcome to 1329 SVN! 🎉 \n\nReply with:\n1 to receive a GIF \n2 for an image \n3 for an SMS!"""

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

from django.core import serializers


# get info for user
def get_user(request, user_id):
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        raise Http404("User does not exist")
    
    return JsonResponse(user.to_json())

#
# -------------------------- FOR TESTING PURPOSES ONLY ----------------------------
#
@csrf_exempt # TODO: address CSRF if deploying to production
def generate_users(request):

    mock_users = [('Doug', 'Q'), ('Kishan', 'P'), ('Abhishek', 'B')]
    for user in mock_users:
        user = CustomUser(first_name = user[0], last_name = user[1])
        user.save()

    return HttpResponse(f"created 3 users!")

@csrf_exempt # TODO: address CSRF if deploying to production
def unmatch_users(request):
    CustomUser.objects.all().update(match_ids=list(), num_matches_found=0)   
    return HttpResponse(f"unmatched all users!")
