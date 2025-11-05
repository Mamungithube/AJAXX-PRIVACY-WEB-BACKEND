from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests
 
@api_view(['GET'])
def get_databrokers_list(request):
    try:
        url = "https://public-api-sandbox.test.optery.com/v1/databrokers/data"
        api_key = "sk_test-f1a8dc62dfd24992a16a62aec5478f1c8588267164b543f297666de6dccc4609"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return Response(
                response.json(),
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "error": "Failed to fetch data from Optery API",
                    "details": response.text
                },
                status=response.status_code
            )
    except requests.exceptions.Timeout:
        return Response(
            {"error": "Request timeout"},
            status=status.HTTP_408_REQUEST_TIMEOUT
        )
    except requests.exceptions.RequestException as e:
        return Response(
            {"error": f"Request failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )