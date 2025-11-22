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

from .serializers import AddMemberSerializer
 
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

@api_view(['GET'])
def get_custom_removals(request):
    try:
        email = request.query_params.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        url = f"https://business.staging.optery.com/custom-removals?email={email}"
        api_key = "YOUR_API_KEY"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            return Response(response.json(), status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "error": "Failed to fetch custom removals",
                    "details": response.text
                },
                status=response.status_code
            )

    except requests.exceptions.Timeout:
        return Response({"error": "Request timeout"}, status=status.HTTP_408_REQUEST_TIMEOUT)

    except requests.exceptions.RequestException as e:
        return Response({"error": f"Request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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







# @method_decorator(csrf_exempt, name='dispatch')
class AddMemberAPIView(APIView):
    """
    APIView for creating new add_member instances.
    Provides only POST method.
    """
    
    def post(self, request, *args, **kwargs):
        serializer = AddMemberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    





OPTERY_BASE = "https://public-api-sandbox.test.optery.com/"
OPTERY_TOKEN = "sk_test-f1a8dc62dfd24992a16a62aec5478f1c8588267164b543f297666de6dccc4609"   # এখানে তোমার স্কি রাখবে


class OpteryCombinedView(APIView):
    def get(self, request):
        member_uuid = request.query_params.get("member_uuid")

        if not member_uuid:
            return Response({"error": "member_uuid is required"}, status=400)

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {OPTERY_TOKEN}"
        }

        # -------------- SAFE JSON PARSE FUNCTION --------------
        def safe_json(res):
            try:
                return res.json()
            except:
                return {"error": "Invalid JSON response", "raw": res.text}

        # ---------------- STEP 1: get-scans --------------------
        scan_url = f"{OPTERY_BASE}v1/optouts/{member_uuid}/get-scans"
        print(f'Fetching scans from: {scan_url}')
        scan_response = requests.get(scan_url, headers=headers)
        scan_res = safe_json(scan_response)

        if "error" in scan_res:
            return Response({"scan_api_error": scan_res}, status=400)

        # scan_id সংগ্রহ
        scan_ids = [item.get("scan_id") for item in scan_res if item.get("scan_id")]

        # ---------------- STEP 2: screenshots -------------------
        screenshots = []
        for scan_id in scan_ids:
            ss_url = f"{OPTERY_BASE}/v1/optouts/{member_uuid}/get-screenshots-by-scan/{scan_id}"
            ss_response = requests.get(ss_url, headers=headers)
            ss_res = safe_json(ss_response)

            screenshots.append({
                "scan_id": scan_id,
                "screenshots": ss_res
            })

        return Response({
            "member_uuid": member_uuid,
            "scans": scan_res,
            "screenshots": screenshots
        })