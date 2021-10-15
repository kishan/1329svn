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

num_matches = 3

def index(request):
    return HttpResponse("Hello, world.")

@csrf_exempt # TODO: address CSRF if deploying to production
def match_users(request):

    # Build a map of all users still in the game.
    all_users = CustomUser.objects.all()
    all_user_ids = [user.id for user in all_users]

    # Only attempt to match users that haven't been matched yet.
    users_not_matched = CustomUser.objects.filter(match_ids__len=0)

    for user in users_not_matched:
        # Generate 3 random matches (1 to N, where N is total) and save to DB
        # TODO: refine this. Right now this biases towards "overmatching" on
        # those who show up a little bit earlier because their user IDs will be available
        # for selection in this process potentialy more than once.
        matches = []
        while len(matches) != 3:
            match = random.choice(all_user_ids)
            if match == user.id or match in matches:
                # Exclude invalid self-matches or matches that we've already made.
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

    # send greeting text
    greeting_msg = f'''
    Hey {first_name}! Welcome to 1329 SVN 🎉
    
Tonight we will be playing a little game — in a few moments you will receive 3 fun facts about others at this party.

These are your matches for the night, and your job is to find them. Once you think you've found them, text us their name and we will try confirm if it's the right person!

Fastest person to find all {num_matches} matches wins a secret prize 🤫
    '''
    # Use actual number from form
    send_sms(phone_num, greeting_msg)

    return HttpResponse(json.dumps({"message":f"user {first_name} added with user_id: {user.id}"}))


# Endpoint for responding to incoming SMS messages to our Twilio number
@require_POST
@csrf_exempt # TODO: address CSRF if deploying to production
def sms_reply(request):

    guess = request.POST.get('Body', '').lower()
    phone_num = request.POST.get('From', '').lower()
    phone_num = phone_num.replace('+1', '') # Remove country code if it's there

    msg_body, media_link = handle_sms_reply(guess, phone_num)

    # Create and send back Twilio response.
    response = MessagingResponse()
    msg = response.message(str(msg_body))
    if media_link:
        msg.media(media_link)
    
    return HttpResponse(response)

# Helper function for handling an SMS reply.
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
        t = datetime.datetime.now(datetime.timezone.utc)
        if len(user.match_found_times) > 0 and user.match_found_times[best_match_idx] != -1:
            # To handle repeated entry of the same correct guess.
            msg_body="""Looks like you already found this match..."""
            return msg_body, media_link

        if not user.match_found_times or len(user.match_found_times) == 0:
            # Initiate new array of match found times.
            user.match_found_times = [-1 for i in range(num_matches)]

        user.match_found_times[best_match_idx] = int(time.time())
        user.num_matches_found += 1
        user.save()
        
        if user.num_matches_found == 1:
            msg_body="""That's correct! Great start to the night. 2 more to go!"""

        elif user.num_matches_found == 2:
            msg_body="""Bingo! Just one more now..."""

        elif user.num_matches_found == 3:
            msg_body="""A,B,C...it's easy as 1,2,3...and that's the number of matches you found! Congratulations on finding all your matches!!! 👏 Thanks for playing and enjoy the rest of the party 🎊"""
            media_link='https://i.pinimg.com/originals/bd/23/5c/bd235c84724d5eb04b5cfe39028e936c.gif'


    elif best_score > 80:
        # Send an encouraging message.
        msg_body="""That was close! Check your spelling and try again?"""

    else:
        msg_body="""Not quite. You might want to expand your search a little..."""

            # TODO: Share on TV that a new match has been found!

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

from django.core import serializers


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

    CustomUser.objects.all().delete()

    mock_users = [
        ('Doug', 'Q', '2039807851'), 
        ('Kishan', 'P', '9783823789'),
        ('Abhishek', 'B', '1'),
        ('George', 'P', '2'),
        ('Anand', 'T', '3'),
    ]
    for user in mock_users:
        user = CustomUser(first_name = user[0], last_name = user[1], phone = user[2])
        user.match_found_times = [-1 for i in range(num_matches)]
        user.save()

    return HttpResponse(f"created users!")

@require_POST
@csrf_exempt # TODO: address CSRF if deploying to production
def verify_guess(request):

    body = json.loads(request.__dict__['environ']['wsgi.input'].read())
    msg_body, _ = handle_sms_reply(body["guess"], body["phone_num"])

    return HttpResponse(msg_body)


@csrf_exempt # TODO: address CSRF if deploying to production
def unmatch_users(request):
    CustomUser.objects.all().update(match_ids=list(), num_matches_found=0)   
    return HttpResponse(f"unmatched all users!")
