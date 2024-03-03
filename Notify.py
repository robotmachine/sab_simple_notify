import requests
import sys
import json
import os
import logging
from pathlib import Path


def notify(message_title: str, message_text: str) -> None:
    """Simple notification tool for SabNZBd+"""
    # Strings to be ignored
    ignore_strings: tuple = ("signal 15", "cannot read watched", "message was ignored")

    creds: dict = get_creds()

    logger: logging = create_logger()

    # Provides nicer looking titles for messages
    message_types: dict = {
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
    if (
        len(
            [
                ignore
                for ignore in ignore_strings
                if ignore.lower() in message_text.lower()
            ]
        )
        > 0
    ):
        quit("Message was ignored")

    # Message style will be "Title .:. Text of Message"
    # If there isn't a nicer looking version of the title, then the user input is used instead
    try:
        message_to_send: str = f"{message_types[message_title]} .:. {message_text}"
    except IndexError:
        message_to_send: str = f"{message_title} .:. {message_text}"

    # Sends messages
    responses: dict = {
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


def get_creds() -> dict:
    """Gets credentials from `creds.json` file in the same dir as this script"""
    cred_file = f"{os.path.dirname(__file__)}/creds.json"
    if Path.exists(Path(cred_file)):
        creds = json.load(open(cred_file))
    else:
        quit(f"Cannot find {cred_file}")
    return creds


def send_pushover(creds: dict, message: str) -> requests:
    """Send message formatted for Pushover API"""
    base_url: str = "api.pushover.net"
    url_endpoint: str = "1/messages.json"
    url: str = f"https://{base_url}/{url_endpoint}"

    querystring: dict = {
        "token": creds["pushover"]["api_token"],
        "user": creds["pushover"]["user_key"],
        "message": message,
    }
    return requests.request("POST", url, data="", params=querystring)


def send_webhook(service: str, creds: dict, message: str) -> requests:
    """Send webhook request"""
    if service.lower() == "slack":
        payload = {"text": message}
    elif service.lower() == "discord":
        payload = {"content": message}
    else:
        quit(f"{service} not supported")
    return requests.post(
        creds[service]["webhook_url"],
        json=payload,
        headers={"Content-Type": "application/json"},
    )


def create_logger() -> logging:
    """Create a formatted logger"""
    log_file = f"{os.path.dirname(__file__)}/Notify.log"
    if not Path.exists(Path(log_file)):
        Path(log_file).touch()
    formatter = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(
        filename=log_file, filemode="a", level=logging.DEBUG, format=formatter
    )
    return logging.getLogger()


if __name__ == "__main__":
    try:
        notify(message_title=sys.argv[1], message_text=sys.argv[3])
    except IndexError:
        notify(message_title="other", message_text="Test message body")
