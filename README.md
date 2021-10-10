# 1329svn

This is a Django project conigured with Twilio.




## How to Setup Project

### 1. Clone the repo
```
git clone git@github.com:<username>/1329svn.git
```

### 2. Create your own virtual environment
  ```
 $ python3 -m venv venv
 $ source venv/bin/activate
```

### 3. Install requirements
`$ pip install -r requirements.txt`

### 4. Set environment variables
Create `.env` file based upon `.env_sample` and fill in variables
```
cp .env_sample .env
```
`DJANGO_SECRET_KEY`: you'll need to generate new secret key. Can use [Djecrety](https://djecrety.ir/) to quickly generate secure secret keys.

`TWILIO_ACCOUNT_SID`: get from twilio.com/console

`TWILIO_AUTH_TOKEN`: get from twilio.com/console

`TWILIO_NUMBER`: use Twilio number you bought. This number is where texts/calls will be recieved from

`TEST_NUMBER`: your personal number that you can use for testing

### 5. Run server
We'll be using [localhost.run](localhost.run) which provides us with a publicly accessible URL to our Django app.
```
  $ python manage.py runserver
  $ ssh -R 80:localhost:8000 localhost.run
```

### 6. Configure Twilio Webhook URLs
We now need to configure our Twilio phone number to call our webhook URLs whenever a new SMS message or call comes in. For your twilio phone number, set the webhook url for Messaging & Voice to the public url obtained above.

- Ex. Voice: https://992df4c7ad12c2.localhost.run/call_answer/
- Ex. Messaging: https://992df4c7ad12c2.localhost.run/sms_reply/

### 7. Give it a test
Test out your server by navingating to `/test_sms` endpoint from the public rul obtained above. 
Note: You will need to add your phone number as a verified number on the Twilio account if you are on a trail plan

Ex. `https://992df4c7ad12c2.localhost.run/test_sms/`