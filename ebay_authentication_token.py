import os
from dotenv import load_dotenv, set_key
import requests
from base64 import b64encode
from urllib.parse import urlparse, parse_qs
import webbrowser

# Load environment variables from .env file
load_dotenv()

# Retrieve eBay production application credentials and redirect URI (RuName) from environment variables
# Make sure these are set in your .env file, e.g.:
# EBAY_CLIENT_ID="your_client_id"
# EBAY_CLIENT_SECRET="your_client_secret"
# EBAY_REDIRECT_URI="your_redirect_uri"
client_id = os.getenv("EBAY_CLIENT_ID")
client_secret = os.getenv("EBAY_CLIENT_SECRET")
redirect_uri = os.getenv("EBAY_REDIRECT_URI")

# Check if credentials were loaded
if not all([client_id, client_secret, redirect_uri]):
    print("Error: EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, or EBAY_REDIRECT_URI not found in .env file or environment variables.")
    print("Please ensure they are set correctly in your .env file as follows:")
    print("EBAY_CLIENT_ID=YOUR_ACTUAL_CLIENT_ID")
    print("EBAY_CLIENT_SECRET=YOUR_ACTUAL_CLIENT_SECRET")
    print("EBAY_REDIRECT_URI=YOUR_ACTUAL_RUNAME")
    exit()

# Define all the scopes based on your requirements
# Example: "scope1 scope2 scope3"
# Ensure scopes are space-separated. Add more from your commented list as needed.
scopes = (
    "https://api.ebay.com/oauth/api_scope "  # Space added here
    "https://api.ebay.com/oauth/api_scope/sell.inventory "
    "https://api.ebay.com/oauth/api_scope/commerce.identity.readonly"
)

# Set the target endpoint for the consent request in production
consent_endpoint_production = "https://auth.ebay.com/oauth2/authorize"
token_endpoint = "https://api.ebay.com/identity/v1/oauth2/token"

# Define the consent URL
consent_url = (
    f"{consent_endpoint_production}?"
    f"client_id={client_id}&"
    f"redirect_uri={redirect_uri}&"
    f"response_type=code&"
    f"scope={scopes}"
)

# Open the consent URL in the default web browser
webbrowser.open(consent_url)

print("Opening the browser. Please grant consent in the browser.")
print(f"If the browser does not open, please manually navigate to: {consent_url}")

# Retrieve the authorization code from the user after they grant consent
authorization_code_url = input("After granting consent, eBay will redirect you. Paste the entire redirect URL here: ")

# Parse the URL to extract the authorization code
try:
    parsed_url = urlparse(authorization_code_url)
    query_params = parse_qs(parsed_url.query)
    authorization_code = query_params.get('code')
    if not authorization_code:
        print("Error: 'code' not found in the redirect URL.")
        if 'error' in query_params:
            error_desc = query_params.get('error_description', query_params.get('error'))
            if error_desc:
                print(f"eBay returned an error: {error_desc[0]}")
            else:
                print(f"eBay returned an error, but no description was provided. Full query: {parsed_url.query}")
        exit()
    authorization_code = authorization_code[0]
except Exception as e:
    print(f"Error parsing the authorization code URL: {e}")
    exit()

# Make the authorization code grant request to obtain the token
payload = {
    "grant_type": "authorization_code",
    "code": authorization_code,
    "redirect_uri": redirect_uri
}

# Encode the client credentials for the Authorization header
credentials = f"{client_id}:{client_secret}"
encoded_credentials = b64encode(credentials.encode()).decode()

# Set the headers for the token request
token_headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": f"Basic {encoded_credentials}"
}

# Make the POST request to the token endpoint
try:
    response = requests.post(token_endpoint, headers=token_headers, data=payload)
    response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)

    # Parse and print the response JSON
    response_json = response.json()
    print("\nResponse containing the User access token and refresh token:")
    print(response_json)

    # You can save these tokens securely, e.g., in a file or environment variables for future use.
    # For example:
    access_token = response_json.get("access_token")
    refresh_token = response_json.get("refresh_token")
    expires_in = response_json.get("expires_in")
    refresh_token_expires_in = response_json.get("refresh_token_expires_in")

    if access_token and refresh_token:
        env_file_path = ".env"
        try:
            set_key(env_file_path, "EBAY_OAUTH_TOKEN", access_token)
            set_key(env_file_path, "EBAY_REFRESH_TOKEN", refresh_token)
            print(f"\nSuccessfully updated {env_file_path} with new tokens.")
        except Exception as e:
            print(f"\nError updating {env_file_path}: {e}")

        # Display first 10 and last 10 chars
        print("\n--- Token Summary ---")
        if len(access_token) > 20:
            print(f"Access Token:   {access_token[:10]}...{access_token[-10:]}")
        else:
            print(f"Access Token:   {access_token}")
        if len(refresh_token) > 20:
            print(f"Refresh Token:  {refresh_token[:10]}...{refresh_token[-10:]}")
        else:
            print(f"Refresh Token:  {refresh_token}")
        print("---------------------")
    else:
        print("\nError: Could not retrieve access_token or refresh_token. .env file not updated.")


    print(f"Access Token Expires In (seconds): {expires_in}")
    print(f"Refresh Token Expires In (seconds): {refresh_token_expires_in}")

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
    print(f"Response content: {response.text}")
except requests.exceptions.RequestException as req_err:
    print(f"Request error occurred: {req_err}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    if 'response' in locals() and hasattr(response, 'text'):
        print(f"Response content: {response.text}")
