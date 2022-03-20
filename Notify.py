import requests
import sys
import json
import os


def main():
    creds = get_creds()
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

    ignore_strings = ["signal 15 caught", "cannot read watched"]  # enter all lower case

    try:
        ignore_strings.index(sys.argv[3].lower())
        quit()
    except ValueError:
        pass

    message = f"{message_types[sys.argv[1]]} .:. {sys.argv[3]}"
    send_pushover(creds, message)
    send_slack(creds, message)


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


if __name__ == "__main__":
    main()
