import requests
import sys
import json
import os
import logging


def main():
    ignore_strings = ["signal 15 caught", "cannot read watched"]  # enter all lower case

    logger = create_logger()  # creates a logger for errors
    creds = get_creds()  # reads from creds.json
    message_types = {  # provides nicer looking type names
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

    try:  # if title doesn't match known type change to test
        message_title = message_types[sys.argv[1]]
    except IndexError:
        logger.info("Using test title")
        message_title = "Test"
    try:  # if no command line arguments are provided it defaults to test message
        message_text = sys.argv[3]
    except IndexError:
        logger.info("Using test text")
        message_text = "Test message"
    if message_text != "Test message":  # check for ignored messages unless it is a test
        try:
            ignore_strings.index(sys.argv[3].lower())
            logging.info("Message was ignored")
            quit()
        except ValueError:  # this means it isn't an ignored message
            pass

    message = f"{message_title} .:. {message_text}"  # Builds message in the style of "Title .:. Message text"

    # Sends messages
    responses = {
        "pushover": send_pushover(creds, message),
        "slack": send_slack(creds, message),
    }
    handle_errors(creds, responses, logger)  # checks responses for errors and logs them to log file
    quit()


def get_creds():
    cred_file = "creds.json"
    if os.path.isfile(cred_file):
        creds = json.load(open(cred_file))
    else:
        quit(f"Cannot find {cred_file}")
    return creds


def send_pushover(creds, message):
    url = "https://api.pushover.net/1/messages.json"

    querystring = {
        "token": creds["pushover"]["api_token"],
        "user": creds["pushover"]["user_key"],
        "message": message,
    }
    payload = ""
    response = requests.request("POST", url, data=payload, params=querystring)
    return response


def send_slack(creds, message):
    response = requests.post(
        creds["slack"]["webhook_url"],
        json={"text": message},
        headers={"Content-Type": "application/json"},
    )
    return response


def handle_errors(creds, responses, logger):
    for app, response in responses.items():
        if int(str(response.status_code)[0]) == 2:
            logger.info(f"{app}: {response.status_code} {response.reason}")
        else:
            logger.critical(f"{app}: {response.status_code} {response.reason}")


def create_logger():
    logger = logging.getLogger("safarijim")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    file_handler = logging.FileHandler(filename="Notify.log", mode="a")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


if __name__ == "__main__":
    main()
