import requests
import os

client_id = os.environ['WP_COM_CLIENT_ID']
client_secret = os.environ['WP_COM_CLIENT_SECRET']
auth_code = os.environ['AUTH_CODE']

response = requests.post("https://public-api.wordpress.com/oauth2/token", data={
    'client_id': client_id,
    'client_secret': client_secret,
    'code': auth_code,
    'redirect_uri': 'https://crop-circuit.com/oauth-callback',
    'grant_type': 'authorization_code'
})

print("REFRESH_TOKEN=", response.json().get('refresh_token'))
