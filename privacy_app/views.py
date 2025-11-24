from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import OpteryScanHistory
from .serializers import OpteryScanHistorySerializer

 
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
    

@api_view(['GET'])
def get_optouts(request):
    try:
        url = "https://public-api-sandbox.test.optery.com/v1/databrokers/data"
        api_key = "sk_test-f1a8dc62dfd24992a16a62aec5478f1c8588267164b543f297666de6dccc4609"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return Response(
                {
                    "error": "Failed to fetch data from Optery API",
                    "details": response.text
                },
                status=response.status_code
            )

        # Full Optery Response
        data = response.json()

        # Extract only plan fields
        plans = []
        for item in data.get("items", []):
            plan = item.get("plan")
            if plan:  # যদি plan থাকে
                plans.append(plan)

        return Response({"plans": plans}, status=status.HTTP_200_OK)

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


@api_view(['POST'])
def optery_webhook(request):
    try:
        event = request.data  # Optery Webhook payload

        # Example: Log event type
        event_type = event.get("type")

        # এখানে তুমি event অনুযায়ী তোমার কাজ করতে পারো
        # যেমন scan completed, removal completed, alert updates ইত্যাদি

        # Example: store to database (optional)
        # WebhookLog.objects.create(payload=event)

        return Response({"status": "received", "event_type": event_type}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)



import requests
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def create_optery_member(request):
    """
    Create a new member in Optery system
    """
    try:
        # Parse request body
        data = json.loads(request.body.decode('utf-8'))
        
        # Log incoming data for debugging
        logger.info(f"Received data: {data}")
        
        # Prepare payload - ensure all fields are properly formatted
        payload = {
            "email": str(data.get("email", "")),
            "first_name": str(data.get("first_name", "")),
            "last_name": str(data.get("last_name", "")),
            "middle_name": str(data.get("middle_name", "")) if data.get("middle_name") else None,
            "city": str(data.get("city", "")),
            "country": str(data.get("country", "US")),
            "state": str(data.get("state", "")),
            "birthday_day": int(data.get("birthday_day")) if data.get("birthday_day") else None,
            "birthday_month": int(data.get("birthday_month")) if data.get("birthday_month") else None,
            "birthday_year": int(data.get("birthday_year")) if data.get("birthday_year") else None,
            "plan": str(data.get("plan", "")),
            "postpone_scan": int(data.get("postpone_scan", 45)),
            "group_tag": data.get("group_tag") if data.get("group_tag") not in [None, "", "None", "null"] else None,
            "address_line1": str(data.get("address_line1", "")) if data.get("address_line1") else None,
            "address_line2": str(data.get("address_line2", "")) if data.get("address_line2") else None,
            "zipcode": str(data.get("zipcode", "")) if data.get("zipcode") else None
        }
        
        # Remove None values if not needed
        # payload = {k: v for k, v in payload.items() if v is not None}
        
        # Log payload being sent
        logger.info(f"Sending payload: {payload}")
        
        # Prepare headers - exactly as in the working script
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.OPTERY_API_KEY}"
        }
        
        # Make API request with explicit json parameter
        response = requests.post(
            settings.OPTERY_API_URL,
            json=payload,  # Use json parameter, not data
            headers=headers,
            timeout=30
        )
        
        # Log response for debugging
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        # Return response
        return JsonResponse({
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "data": response.json() if response.text else {},
            "sent_payload": payload  # Include for debugging
        }, status=response.status_code)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": f"Invalid JSON in request body: {str(e)}"
        }, status=400)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": f"API request failed: {str(e)}"
        }, status=500)
        
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": f"Invalid data format: {str(e)}"
        }, status=400)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }, status=500)


# Class-based view alternative
from django.views import View
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name='dispatch')
class OpteryMemberView(View):
    """Class-based view for Optery member operations"""
    
    def post(self, request):
        """Create a new Optery member"""
        try:
            data = json.loads(request.body)
            
            payload = {
                "email": data.get("email"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "middle_name": data.get("middle_name"),
                "city": data.get("city"),
                "country": data.get("country", "US"),
                "state": data.get("state"),
                "birthday_day": data.get("birthday_day"),
                "birthday_month": data.get("birthday_month"),
                "birthday_year": data.get("birthday_year"),
                "plan": data.get("plan"),
                "postpone_scan": data.get("postpone_scan", 45),
                "group_tag": data.get("group_tag"),
                "address_line1": data.get("address_line1"),
                "address_line2": data.get("address_line2"),
                "zipcode": data.get("zipcode")
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {settings.OPTERY_API_KEY}"
            }
            
            response = requests.post(
                settings.OPTERY_API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            return JsonResponse({
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "data": response.json()
            }, status=response.status_code)
            
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "error": "Invalid JSON in request body"
            }, status=400)
            
        except requests.exceptions.RequestException as e:
            return JsonResponse({
                "success": False,
                "error": f"API request failed: {str(e)}"
            }, status=500)
            
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": f"Internal server error: {str(e)}"
            }, status=500)

    


OPTERY_BASE = "https://public-api-sandbox.test.optery.com/"
OPTERY_TOKEN = "sk_test-f1a8dc62dfd24992a16a62aec5478f1c8588267164b543f297666de6dccc4609"  


class OpteryCombinedView(APIView):
    def get(self, request):
        member_uuid = request.query_params.get("member_uuid")

        if not member_uuid:
            return Response({"error": "member_uuid is required"}, status=400)

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {OPTERY_TOKEN}"
        }

        # Safe JSON parser
        def safe_json(res):
            try:
                return res.json()
            except:
                return {"error": "Invalid JSON response", "raw": res.text}

        # STEP 1: Get scans
        scan_url = f"{OPTERY_BASE}v1/optouts/{member_uuid}/get-scans"
        scan_response = requests.get(scan_url, headers=headers)
        
        # Check HTTP status first
        if scan_response.status_code != 200:
            return Response({
                "error": f"Scan API returned status {scan_response.status_code}",
                "details": scan_response.text
            }, status=scan_response.status_code)
            
        scan_res = safe_json(scan_response)

        # -----------------------------
        # Improved Validation: Handle both list and error response
        # -----------------------------
        if isinstance(scan_res, dict) and scan_res.get("error"):
            # API returned an error in JSON format
            return Response({
                "scan_api_error": scan_res.get("error"),
                "raw": scan_res
            }, status=400)
            
        if not isinstance(scan_res, list):
            # If it's not a list and not an error, it's unexpected format
            return Response({
                "scan_api_error": "Invalid scan response format. Expected list.",
                "received_type": type(scan_res).__name__,
                "raw_response": scan_res
            }, status=400)

        # Collect scan IDs safely
        scan_ids = []
        for item in scan_res:
            if isinstance(item, dict) and item.get("scan_id"):
                scan_ids.append(item.get("scan_id"))

        # If no scan IDs found
        if not scan_ids:
            return Response({
                "message": "No scans found for this member",
                "member_uuid": member_uuid,
                "scans": scan_res
            }, status=200)

        screenshots = []

        for scan_id in scan_ids:
            # Fixed URL - added missing slash
            # ss_url = f"{OPTERY_BASE}/v1/optouts/{member_uuid}/get-screenshots-by-scan/{scan_id}"
            ss_url = f"{OPTERY_BASE}v1/optouts/{member_uuid}/get-screenshots-by-scan/{scan_id}"
            ss_response = requests.get(ss_url, headers=headers)
            
            # Check screenshot API response status
            if ss_response.status_code == 200:
                ss_res = safe_json(ss_response)
            else:
                ss_res = {"error": f"API returned {ss_response.status_code}", "raw": ss_response.text}

            screenshots.append({
                "scan_id": scan_id,
                "screenshots": ss_res
            })

            # Save history safely with error handling
            try:
                OpteryScanHistory.objects.create(
                    member_uuid=member_uuid,
                    scan_id=scan_id,
                    raw_scan_data=scan_res,
                    raw_screenshot_data=ss_res
                )
            except Exception as e:
                # Log the error but don't break the flow
                print(f"Failed to save history for scan {scan_id}: {str(e)}")

        return Response({
            "member_uuid": member_uuid,
            "scans": scan_res,
            "screenshots": screenshots,
            "message": "Data fetched & history saved!"
        })



from rest_framework.views import APIView
from rest_framework.response import Response
from .models import OpteryScanHistory

class OpteryHistoryListView(APIView):
    def get(self, request):
        member_uuid = request.query_params.get("member_uuid")

        if not member_uuid:
            return Response({"error": "member_uuid is required"}, status=400)

        histories = OpteryScanHistory.objects.filter(member_uuid=member_uuid).order_by("-created_at")

        data = [
            {
                "id": h.id,
                "member_uuid": h.member_uuid,
                "scan_id": h.scan_id,
                "raw_scan_data": h.raw_scan_data,
                "raw_screenshot_data": h.raw_screenshot_data,
                "created_at": h.created_at
            }
            for h in histories
        ]

        return Response({"history": data})
    




    # REmove data

class CustomRemovalListView(APIView):
    def get(self, request):
        member_uuid = "58da6057-e228-437f-8e08-da3be86d74dd"

        url = f"https://public-api-sandbox.test.optery.com/v1/optouts/{member_uuid}/custom-removals"
        
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer sk_test-f1a8dc62dfd24992a16a62aec5478f1c8588267164b543f297666de6dccc4609"
        }

        res = requests.get(url, headers=headers)

        return Response(res.json())
    



class CustomRemovalCreateView(APIView):
    def post(self, request):

        # QUERY PARAM থেকে UUID নিন
        member_uuid = request.GET.get("member_uuid")

        if not member_uuid:
            return Response({"error": "member_uuid is required as query parameter"}, status=400)

        # এখন Optery API-তে PATH PARAM পাঠাবেন
        url = f"https://public-api-sandbox.test.optery.com/v1/optouts/{member_uuid}/custom-removals"

        exposed_url = request.data.get("exposed_url")
        search_engine_url = request.data.get("search_engine_url")
        search_keywords = request.data.get("search_keywords")
        additional_information = request.data.get("additional_information")
        proof_file = request.FILES.get("proof_of_exposure")

        if not exposed_url or not proof_file:
            return Response(
                {"error": "exposed_url & proof_of_exposure are required"},
                status=400
            )

        data = {
            "exposed_url": exposed_url,
            "search_engine_url": search_engine_url,
            "search_keywords": search_keywords,
            "additional_information": additional_information,
        }

        files = {
            "proof_of_exposure": (
                proof_file.name,
                proof_file.read(),
                proof_file.content_type
            )
        }

        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer sk_test-f1a8dc62dfd24992a16a62aec5478f1c8588267164b543f297666de6dccc4609",
        }

        api_res = requests.post(url, data=data, files=files, headers=headers)

        # JSON error safe
        try:
            return Response(api_res.json(), status=api_res.status_code)
        except ValueError:
            return Response(
                {"error": "Invalid JSON from Optery", "raw": api_res.text},
                status=500
            )
