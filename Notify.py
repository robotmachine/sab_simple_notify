import requests
import sys
import json
import os
import logging
from pathlib import Path


def notify(message_title, message_text):
    """Simple notification tool for SabNZBd+"""
    # Strings to be ignored
    ignore_strings = ("signal 15", "cannot read watched")

    creds = get_creds()

    logger = create_logger()

    # Provides nicer looking titles for messages
    message_types = {
        "startup": "Startup/Shutdown",
        "download": "Added NZB",
        "pp": "Post-processing started",
        "complete": "Job finished",
        "failed": "Job failed",
        "warning": "Warning",
        "error": "Error",
        "disk_full": "Disk full",
        "queue_done": "Queue finished",
        "new_login": "User logged in",
        "other": "Other Messages",
    }

    # Handle ignoring of unwanted messages
    if len([ignore for ignore in ignore_strings if ignore.lower() in message_text.lower()]) > 0:
        quit('Message was ignored')

    # Message style will be "Title .:. Text of Message"
    # If there isn't a nicer looking version of the title, then the user input is used instead
    try:
        message_to_send = f"{message_types[message_title]} .:. {message_text}"
    except IndexError:
        message_to_send = f"{message_title} .:. {message_text}"

    # Sends messages
    responses = {
        "pushover": send_pushover(creds, message_to_send),
        # "slack": send_webhook("slack", creds, message),
        "discord": send_webhook("discord", creds, message_to_send),
    }

    # Does error checking
    for app, response in responses.items():
        if response.ok:
            logger.info(f"{app}: {response.status_code} {response.reason}")
        else:
            logger.warning(f"{app}: {response.status_code} {response.reason}")
    quit()


def get_creds():
    """Gets credentials from `creds.json` file in the same dir as this script"""
    cred_file = f"{os.path.dirname(__file__)}/creds.json"
    if Path.exists(Path(cred_file)):
        creds = json.load(open(cred_file))
    else:
        creds = None
        quit(f"Cannot find {cred_file}")
    return creds


def send_pushover(creds, message):
    """Send message formatted for Pushover API"""
    base_url = "api.pushover.net"
    url_endpoint = "1/messages.json"
    url = f"https://{base_url}/{url_endpoint}"

    querystring = {
        "token": creds["pushover"]["api_token"],
        "user": creds["pushover"]["user_key"],
        "message": message,
    }
    return requests.request("POST", url, data="", params=querystring)


def send_webhook(service, creds, message):
    """Send webhook request"""
    if service.lower() == 'slack':
        payload = {'text': message}
    elif service.lower() == 'discord':
        payload = {'content': message}
    else:
        payload = None
        quit(f'{service} not supported')
    return requests.post(
        creds[service]["webhook_url"],
        json=payload,
        headers={"Content-Type": "application/json"},
    )


def create_logger():
    """Create a formatted logger"""
    log_file = f"{os.path.dirname(__file__)}/Notify.log"
    if not Path.exists(Path(log_file)):
        Path(log_file).touch()
    formatter = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(filename=log_file, filemode="a", level=logging.DEBUG, format=formatter)
    return logging.getLogger()


if __name__ == "__main__":
    try:
        notify(message_title=sys.argv[1], message_text=sys.argv[3])
    except IndexError:
        notify(message_title="other", message_text="Test message body")
