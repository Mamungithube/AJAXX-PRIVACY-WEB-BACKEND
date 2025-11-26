    # path("api/get_databrokers_list/", views.get_databrokers_list, name="get-brokers-list"),
    # path("optery/scans/", views.get_optouts, name="get-scans"),
    # path("optery/custom-removals/", views.get_custom_removals, name="get-custom-removals"),
    # path("optery/webhook/", views.optery_webhook, name="optery_webhook"),
    # path("optery/add-member/", views.AddOpteryMember.as_view()),


# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# import requests
# import requests
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .models import OpteryScanHistory
# from .serializers import OpteryScanHistorySerializer
# import requests
# import logging
# from django.conf import settings
# from django.http import JsonResponse
# from django.views.decorators.http import require_http_methods
# from django.views.decorators.csrf import csrf_exempt
# import json

# logger = logging.getLogger(__name__)


# @api_view(['GET'])
# def get_databrokers_list(request):
#     try:
#         url = "https://public-api-sandbox.test.optery.com/v1/databrokers/data"
#         api_key = "sk_test-f1a8dc62dfd24992a16a62aec5478f1c8588267164b543f297666de6dccc4609"
#         headers = {
#             "Accept": "application/json",
#             "Authorization": f"Bearer {api_key}"
#         }
#         response = requests.get(url, headers=headers, timeout=10)
#         if response.status_code == 200:
#             return Response(
#                 response.json(),
#                 status=status.HTTP_200_OK
#             )
#         else:
#             return Response(
#                 {
#                     "error": "Failed to fetch data from Optery API",
#                     "details": response.text
#                 },
#                 status=response.status_code
#             )
#     except requests.exceptions.Timeout:
#         return Response(
#             {"error": "Request timeout"},
#             status=status.HTTP_408_REQUEST_TIMEOUT
#         )
#     except requests.exceptions.RequestException as e:
#         return Response(
#             {"error": f"Request failed: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
#     except Exception as e:
#         return Response(
#             {"error": f"An error occurred: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )
    

# @api_view(['GET'])
# def get_optouts(request):
#     try:
#         url = "https://public-api-sandbox.test.optery.com/v1/databrokers/data"
#         api_key = "sk_test-f1a8dc62dfd24992a16a62aec5478f1c8588267164b543f297666de6dccc4609"

#         headers = {
#             "Accept": "application/json",
#             "Authorization": f"Bearer {api_key}"
#         }

#         response = requests.get(url, headers=headers, timeout=10)

#         if response.status_code != 200:
#             return Response(
#                 {
#                     "error": "Failed to fetch data from Optery API",
#                     "details": response.text
#                 },
#                 status=response.status_code
#             )

#         # Full Optery Response
#         data = response.json()

#         # Extract only plan fields
#         plans = []
#         for item in data.get("items", []):
#             plan = item.get("plan")
#             if plan:  # যদি plan থাকে
#                 plans.append(plan)

#         return Response({"plans": plans}, status=status.HTTP_200_OK)

#     except requests.exceptions.Timeout:
#         return Response(
#             {"error": "Request timeout"},
#             status=status.HTTP_408_REQUEST_TIMEOUT
#         )

#     except requests.exceptions.RequestException as e:
#         return Response(
#             {"error": f"Request failed: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

#     except Exception as e:
#         return Response(
#             {"error": f"An error occurred: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )


# Not Testing 

# @api_view(['GET'])
# def get_custom_removals(request):
#     try:
#         email = request.query_params.get("email")
#         if not email:
#             return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

#         url = f"https://business.staging.optery.com/custom-removals?email={email}"
#         api_key = "YOUR_API_KEY"

#         headers = {
#             "Accept": "application/json",
#             "Authorization": f"Bearer {api_key}"
#         }

#         response = requests.get(url, headers=headers, timeout=10)

#         if response.status_code == 200:
#             return Response(response.json(), status=status.HTTP_200_OK)
#         else:
#             return Response(
#                 {
#                     "error": "Failed to fetch custom removals",
#                     "details": response.text
#                 },
#                 status=response.status_code
#             )

#     except requests.exceptions.Timeout:
#         return Response({"error": "Request timeout"}, status=status.HTTP_408_REQUEST_TIMEOUT)

#     except requests.exceptions.RequestException as e:
#         return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     except Exception as e:
#         return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# @api_view(['POST'])
# def optery_webhook(request):
#     try:
#         event = request.data  # Optery Webhook payload

#         # Example: Log event type
#         event_type = event.get("type")

#         # এখানে তুমি event অনুযায়ী তোমার কাজ করতে পারো
#         # যেমন scan completed, removal completed, alert updates ইত্যাদি

#         # Example: store to database (optional)
#         # WebhookLog.objects.create(payload=event)

#         return Response({"status": "received", "event_type": event_type}, status=200)

#     except Exception as e:
#         return Response({"error": str(e)}, status=400)