import json
import random
import time
import datetime

from django.http import HttpResponse
from django.http import Http404
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from fuzzywuzzy import fuzz

from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse

from matching.models import CustomUser

from .lib_twilio import send_sms, make_call

def index(request):
    return HttpResponse("Hello, world.")

"""
Handles a new form submission by creating user in DB and sending a greeting message.
Will also generate matches if that part of that night has started.
"""
#@require_POST
@csrf_exempt # TODO: address CSRF if deploying to production
def add_user(request):

    # Parse request -> extract name, phone number, and fun fact
    body = request.__dict__['environ']['wsgi.input'].read()

    params = json.loads(body)
    first_name = params['first_name']
    last_name = params['last_name']
    phone_num = params['phone_number']
    fun_fact = params['fun_fact']

    # Create new user in DB
    user = CustomUser(phone = phone_num, first_name = first_name, last_name = last_name, fun_fact = fun_fact)
    user.save()

    # send greeting text
    greeting_msg = f'''
    Hey {first_name}! Welcome to 1329 SVN 🎉
    
Tonight we will be playing a little game — in a few moments you will receive a fun fact about someone else at this party.

Your job is to find who you've been matched to. Once you think you've found them, text us their name and we will try confirm if it's the right person!

Those who find their match get a nice prize at the end... 🤫
    '''
    # Use actual number from form
    send_sms(phone_num, greeting_msg)

    users_matched = CustomUser.objects.filter(match_ids__len__gt=0)
    if len(users_matched) > 0:
        # User matching has initiated. Match every new user.
        match_single_user(user)

    return HttpResponse(json.dumps({"message":f"user {first_name} added with user_id: {user.id}"}))

"""
Matches all users that haven't been matched yet.
"""
@csrf_exempt # TODO: address CSRF if deploying to production
def match_users(request):

    # Only attempt to match users that haven't been matched yet.
    users_not_matched = CustomUser.objects.filter(match_ids__len=0)

    for user in users_not_matched:
        match_single_user(user)

    return HttpResponse(f"matched all users!")

"""
Finds match for a single user and saves result to DB.
Takes as input user and assumes that user currently has no matches.
"""
def match_single_user(user):

    # Generate a list of all users sorted by the number of matches
    all_users_by_match = sorted(CustomUser.objects.all(), key = lambda x: x.num_matched_to_me)

    match_id = None
    for potential_match in all_users_by_match:
        if potential_match.id == user.id:
            # Exclude invalid self-matches or matches that we've already made.
            continue
        match_id = potential_match.id

    user.match_ids = [match_id]
    user.match_create_times = [int(time.time())]
    user.save()

    matched_user = CustomUser.objects.get(pk=match_id)
    matched_user.num_matched_to_me += 1
    matched_user.save()

    # Find fun fact about match and send text notification
    return send_matches(user, matched_user)

"""
Given a user A and who they're matched to (user B), send SMS to user A with fun fact about user B.
"""
def send_matches(user, matched_user):

    match_msg = f'''
Here is the fun fact about your match:

🤔 {matched_user.fun_fact}

Text us their name when you think you've found them!'''

    print(match_msg)

    send_sms(user.phone_num, match_msg)
    return

"""
Handles all incoming text messages to the Twilio bot.
"""
# Endpoint for responding to incoming SMS messages to our Twilio number
@require_POST
@csrf_exempt # TODO: address CSRF if deploying to production
def sms_reply(request):
    incoming_msg = request.POST.get('Body', '').lower()
    if incoming_msg == "yo":
        response = MessagingResponse()
        msg_body = "yoooo"
        msg = response.message(str(msg_body))
        return HttpResponse(response)

    phone_num = request.POST.get('From', '').lower()
    phone_num = phone_num.replace('+1', '') # Remove country code if it's there

    print("Twilio body: ", incoming_msg)
    print("Twilio phone #: ", phone_num)

    msg_body, media_link = handle_sms_reply(incoming_msg, phone_num)

    # Create and send back Twilio response.
    response = MessagingResponse()
    msg = response.message(str(msg_body))
    if media_link:
        msg.media(media_link)
    
    return HttpResponse(response)

"""
Helper function for handling an SMS reply.
"""
def handle_sms_reply(guess, phone_num):

    # Try to fetch user from DB first.
    user = None
    try:
        user = CustomUser.objects.filter(phone=phone_num)[0]
    except CustomUser.DoesNotExist:
        raise Http404("User does not exist")
    
    msg_body = ''
    media_link = ''

    if not user.match_ids or len(user.match_ids) == 0:
        # Matches have not been generated yet for user. Don't attempt to evaluate guess.
        msg_body="""We'll be generating matches soon. Have a drink on us in the meantime 🍹"""
        media_link = 'https://c.tenor.com/wdv_JiOkBGgAAAAC/cheers-lets-drink.gif'
        return msg_body, media_link

    best_match = None
    best_match_idx = -1
    best_score = -1

    for i, match_id in enumerate(user.match_ids):

        # Compute a score on the match.
        potential_match = CustomUser.objects.get(pk=int(match_id))
        score = get_match_score(potential_match, guess)

        print(f"Matching {user} against {potential_match}: {score}...")
            
        if score > best_score:
            best_score = score
            best_match = potential_match
            best_match_idx = i

    print(f"Best match found on {best_match}: {best_score}...")

    if best_score > 90:
        # Consider this a match. Log current time so we can track who
        # found their matches the fastest.
        if len(user.match_found_times) > 0 and user.match_found_times[best_match_idx] != -1:
            # To handle repeated entry of the same correct guess.
            msg_body="""Looks like you already found your match! Go enjoy the party!"""
            return msg_body, media_link

        if not user.match_found_times or len(user.match_found_times) == 0:
            # Initiate new array of match found times.
            user.match_found_times = [-1]

        user.match_found_times[best_match_idx] = int(time.time())
        user.num_matches_found += 1
        user.save()
        
        time_diff = (user.match_found_times[best_match_idx] - user.match_create_times[best_match_idx]) / 60

        msg_body="Congratulations on finding your match in {:.1f} minutes!!! 👏 Thanks for playing 🎊".format(time_diff)
        media_link='https://i.pinimg.com/originals/bd/23/5c/bd235c84724d5eb04b5cfe39028e936c.gif'    

    elif best_score > 80:
        # Send an encouraging message.
        msg_body="""That was close! Check your spelling and try again?"""

    else:
        msg_body="""Not quite. You might want to expand your search a little..."""

    return msg_body, media_link

# Uses fuzzy matching to see if user's guess matches their matches full name in DB.
def get_match_score(user, guess_name):
    
    return fuzz.ratio(f"{user.first_name}".upper(), guess_name.upper())

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

# get info for user
def get_user(request, user_id):
    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        raise Http404("User does not exist")
    
    return JsonResponse(user.to_json())

@csrf_exempt # TODO: address CSRF if deploying to production
def get_leaderboard(request):

    users = list(CustomUser.objects.all())
    leaderboard = sorted(users, key = lambda x: (x.num_matches_found, sum([-s for s in x.match_found_times])), reverse=True)

    leaderboard_json = []
    for user in leaderboard:
        found_times = []
        for ts in user.match_found_times:
            if ts == -1:
                continue
            found_times.append(datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'))
        leaderboard_json.append({
            "User": f'{user.first_name} {user.last_name}',
            "Num Matches Found": user.num_matches_found,
            "Times": found_times,
        })

    return HttpResponse(json.dumps(leaderboard_json))


#
# -------------------------- FOR TESTING PURPOSES ONLY ----------------------------
#
@csrf_exempt # TODO: address CSRF if deploying to production
def generate_users(request):

    delete_users(request)

    mock_users = [
        ('Doug', 'Q', '2039807851'), 
        ('Kishan', 'P', '9783823789'),
        ('Abhishek', 'B', '1'),
        ('George', 'P', '2'),
        ('Anand', 'T', '3'),
    ]
    for user in mock_users:
        user = CustomUser(first_name = user[0], last_name = user[1], phone = user[2])
        user.match_found_times = [-1]
        user.save()

    return HttpResponse(f"created users!")

@require_POST
@csrf_exempt # TODO: address CSRF if deploying to production
def verify_guess(request):

    body = json.loads(request.__dict__['environ']['wsgi.input'].read())
    msg_body, _ = handle_sms_reply(body["guess"], body["phone_num"])

    return HttpResponse(msg_body)

@csrf_exempt
def delete_users(request):
    CustomUser.objects.all().delete()

@csrf_exempt # TODO: address CSRF if deploying to production
def unmatch_users(request):
    CustomUser.objects.all().update(match_ids=list(), num_matches_found=0)   
    return HttpResponse(f"unmatched all users!")
