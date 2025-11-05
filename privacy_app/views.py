from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import requests


def call_optery_api(endpoint, params=None):
    url = f"{settings.OPTERY_BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {settings.OPTERY_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers, params=params)

    try:
        data = response.json()
    except ValueError:
        data = {"error": "Invalid JSON response"}

    return {
        "status_code": response.status_code,
        "data": data
    }


def get_user_privacy_info(email):
    params = {"email": email}
    return call_optery_api("privacy-scan", params)  # ✅ correct endpoint example


class PrivacyInfoView(APIView):
    def get(self, request, email):
        result = get_user_privacy_info(email)
        return Response(result)
