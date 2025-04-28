# authentication/utils.py (Create this file)

import random
import string
import os
from django.utils import timezone
import requests
import json
from okada_backend.settings import ARKESEL_API_KEY
# --- Arkesel API Endpoints ---
ARKESEL_OTP_GENERATE_URL = "https://sms.arkesel.com/api/otp/generate"
ARKESEL_OTP_VERIFY_URL = "https://sms.arkesel.com/api/otp/verify" # Placeholder - Verify actual URL

def send_otp_sms(phone_number):
    """
    Requests OTP generation and sending via Arkesel SMS API.
    Takes phone_number directly.
    """
    if not ARKESEL_API_KEY:
        print("Error: Arkesel API Key not configured in settings.")
        return False
    if not phone_number:
        print("Error: Phone number not provided.")
        return False
    
    


    client = requests.Session()
    headers = {
        "api-key": ARKESEL_API_KEY,
    }
    request_body = {
        "number": phone_number,
        "expiry": "5", 
        "length": "6",
        "medium": "sms",
        "message": "Your Okada verification code is: %otp_code%", # Customize message
        "sender_id": "OkadaGh", 
        "type": "numeric" 
    }


    try:
        response = client.post(ARKESEL_OTP_GENERATE_URL, headers=headers, json=request_body)
        print(response)
        response.raise_for_status() 
       
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error sending OTP request to Arkesel for {phone_number}: {e}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred in send_otp_sms for {phone_number}: {e}")


def verify_otp_arkesel(phone_number, otp_code):
    """
    Verifies the submitted OTP code via Arkesel API.
    Returns True if verification is successful, False otherwise.
    NOTE: This assumes Arkesel provides a verification endpoint.
          The URL and request/response format are placeholders.
    """
    if not ARKESEL_API_KEY:
        print("Error: Arkesel API Key not configured in settings.")
        return False

    print(f"Attempting to verify OTP {otp_code} for: {phone_number}") # Logging

    client = requests.Session()
    headers = {
        "api-key": ARKESEL_API_KEY,
    }
    request_body = {
        "number": phone_number,
        "code": otp_code,
    }

    try:
        response = client.post(ARKESEL_OTP_VERIFY_URL, headers=headers, json=request_body)
        response.raise_for_status()
        print(f"Arkesel Verify OTP Response for {phone_number}: {response.status_code} - {response.text}")

      
        response_data = response.json()
        if response_data.get("message") == "Verification successful" or response_data.get("status") == "success": # Adjust condition
             print(f"OTP verification successful for {phone_number}.")
             return True
        else:
             print(f"OTP verification failed for {phone_number}: {response_data}")
             return False

    except requests.exceptions.RequestException as e:
        print(f"Error verifying OTP with Arkesel for {phone_number}: {e}")
        return False
    except Exception as e:
        print (f"Sending OTP to {phone_number} via Arkesel") # Logging
        print(f"An unexpected error occurred in verify_otp_arkesel for {phone_number}: {e}")
        return False

