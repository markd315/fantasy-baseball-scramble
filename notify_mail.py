def sendMail(to, body, subject="it works", from_name="Fantasy Scramble"):
    # Replace YOUR_API_KEY with your actual API key
        import os
        API_KEY = os.getenv('sendinblue_API_KEY')
        import json
        import requests

        # Set the API endpoint URL
        url = 'https://api.sendinblue.com/v3/smtp/email'

        # Set the email parameters
        payload = {
            "sender": {
                "name": from_name,
                "email": "fantasyscramble@sendinblue.com"
            },
            'to': [{'email': to}],
            'subject': subject,
            'htmlContent': '<p>' + body + '</p>'
        }

        # Set the headers
        headers = {
            'Content-Type': 'application/json',
            'api-key': API_KEY
        }

        # Send the request
        response = requests.post(url, json=payload, headers=headers)

        # Print the response
        print(response.text)


if __name__ == "__main__":
    sendMail("markd315@gmail.com", "mailstop")
