import os
import sys
import json
import logging
import requests
from flask import Flask, request
try:
    from behaviour import answer
except ImportError:
    from .behaviour import answer

app = Flask(__name__)

# Cài đặt logging
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.INFO)

# store env variable value into app's config
app.config.update(VERIFY_TOKEN=os.getenv("VERIFY_TOKEN", None),
                  PAGE_ACCESS_TOKEN=os.getenv("PAGE_ACCESS_TOKEN", None),
                  FACEBOOK_MESSAGING_ENDPOINT="https://graph.facebook.com/v2.6/me/messages")


@app.route('/', methods=['GET'])
def webhook_verification():
    if request.args.get('hub.mode', None) == 'subscribe':
        if request.args.get('hub.challenge', None):
            if not request.args.get("hub.verify_token") == app.config['VERIFY_TOKEN']:
                # VERIFY_TOKEN  is not matches
                app.logger.warning('webhook verification faild: {}'.format(str(requests.args)))
                return "Unauthorized: VERIFY TOKEN is not matching", 403
            # webhook verification OK
            app.logger.info('Webhook verification successful: {}'.format(str(request.args)))
            return request.args['hub.challenge'], 200
    else:
        # trong truong hop mot simple get
        return "Hello, I am a bot of Nguyên", 200


@app.route('/', methods=['POST'])
def webhook():
    awaiting_message = list()

    # extract messages from request data
    data = request.get_json()

    # if it was not a page envent, quit
    if data['object'] != "page":
        return "OK", 200

    # interate over page events
    for entry in data['entry']:
        for message in entry['messaging']:
            # check if there is a text messages
            if message.get('message'):
                # Facebook ID of the user that sent the message
                sender_id = message["sender"]["id"]
                # Text of the message
                text = message['message']['text']
                app.logger.info('Received message from sender: {} with text: {}'.format(sender_id,
                                                                                        text))
                awaiting_message.append((sender_id, text))

    # answer the QUESTION:
    for sender_id, text in awaiting_message:
        response_str = answer(text)
        app.logger.info("Replying to sender: {} with text: {}".format(
            sender_id, response_str))
        reply(sender_id, response_str)
    # phai luon return ra 200
    return "OK", 200


def reply(recipient_id, response_text):
    params = {
        "access_token": app.config["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps(
        {
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": response_text
            }
        }
    )
    r = requests.post(app.config['FACEBOOK_MESSAGING_ENDPOINT'],
                      params=params, headers=headers, data=data)
    if r.status_code != 200:
        app.logger.error('Error in sending response - status: {}, resion: {}'.format(r.status_code,
                                                                                     r.text))


if __name__ == "__main__":
    app.run(debug=True)
