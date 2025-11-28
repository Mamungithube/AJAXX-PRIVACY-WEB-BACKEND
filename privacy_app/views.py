import os
import json
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views import View
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from .models import OpteryScanHistory

# Configure logger
logger = logging.getLogger(__name__)


# Optery API Configuration
OPTERY_BASE_URL = os.getenv('OPTERY_BASE_URL')
OPTERY_API_KEY = os.getenv('OPTERY_API_TOKEN')

def get_optery_config():
    """Safely get Optery configuration from environment with validation"""
    base_url = getattr(settings, 'OPTERY_BASE_URL', OPTERY_BASE_URL)
    api_token = getattr(settings, 'OPTERY_API_KEY', OPTERY_API_KEY)
    
    if not base_url or not api_token:
        logger.error("Optery configuration missing. Check environment variables.")
        raise ValueError("Optery API configuration not found")
    
    # Ensure base URL ends with slash
    if not base_url.endswith('/'):
        base_url += '/'
    
    return base_url, api_token

def safe_json_parse(text, default=None):
    """Safely parse JSON with comprehensive error handling"""
    if not text or not text.strip():
        return default
        
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {str(e)} - Text: {text[:100]}...")
        return default
    except Exception as e:
        logger.error(f"Unexpected JSON parse error: {str(e)}")
        return default

def validate_required_fields(data, required_fields):
    """Validate required fields in request data"""
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    return True


@csrf_exempt
@require_http_methods(["POST"])
def create_optery_member(request):
    try:
        OPTERY_BASE_URL = getattr(settings, 'OPTERY_BASE_URL', os.getenv('OPTERY_BASE_URL'))
        OPTERY_API_TOKEN = getattr(settings, 'OPTERY_API_KEY', os.getenv('OPTERY_API_TOKEN'))
        
        if not OPTERY_BASE_URL or not OPTERY_API_TOKEN:
            return JsonResponse({"success": False, "error": "Service configuration error"}, status=500)

        if not OPTERY_BASE_URL.endswith('/'):
            OPTERY_BASE_URL += '/'

        if not request.body:
            return JsonResponse({"success": False, "error": "Empty request body"}, status=400)

        try:
            data = json.loads(request.body.decode('utf-8'))
        except:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        required_fields = ['email', 'first_name', 'last_name', 'plan']
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return JsonResponse({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }, status=400)

        payload = {
            "email": data["email"].strip().lower(),
            "first_name": data["first_name"].strip(),
            "last_name": data["last_name"].strip(),
            "middle_name": data.get("middle_name"),
            "city": data.get("city"),
            "country": data.get("country", "US"),
            "state": data.get("state"),
            "birthday_day": data.get("birthday_day"),
            "birthday_month": data.get("birthday_month"),
            "birthday_year": data.get("birthday_year"),
            "plan": data["plan"],
            "postpone_scan": data.get("postpone_scan", 45),
            "group_tag": data.get("group_tag"),
            "address_line1": data.get("address_line1"),
            "address_line2": data.get("address_line2"),
            "zipcode": data.get("zipcode"),
        }

        payload = {k: v for k, v in payload.items() if v not in [None, "", "null"]}

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {OPTERY_API_TOKEN}",
        }

        full_url = f"{OPTERY_BASE_URL}v1/members"
        response = requests.post(full_url, json=payload, headers=headers)

        try:
            response_data = response.json()
        except:
            response_data = {"raw_text": response.text}

        is_success = response.status_code in [200, 201]

        # ---------------------------------------------
        # ✅ SAVE INTO DATABASE (IMPORTANT PART)
        # ---------------------------------------------

        member = OpteryMember.objects.create(
            uuid=response_data.get("uuid") or uuid.uuid4(),   # If Optery returns UUID use it
            email=payload["email"],
            first_name=payload["first_name"],
            last_name=payload["last_name"],
            middle_name=payload.get("middle_name"),
            city=payload.get("city"),
            country=payload.get("country", "US"),
            state=payload.get("state"),
            birthday_day=payload.get("birthday_day"),
            birthday_month=payload.get("birthday_month"),
            birthday_year=payload.get("birthday_year"),
            plan=payload["plan"],
            postpone_scan=payload.get("postpone_scan", 45),
            group_tag=payload.get("group_tag"),
            address_line1=payload.get("address_line1"),
            address_line2=payload.get("address_line2"),
            zipcode=payload.get("zipcode"),

            # Save API response details
            optery_response=response_data,
            status_code=response.status_code,
            is_success=is_success
        )

        return JsonResponse({
            "success": is_success,
            "status_code": response.status_code,
            "member_uuid": str(member.uuid),
            "optery_response": response_data
        }, status=response.status_code)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


# Class-based view alternative
# @method_decorator(csrf_exempt, name='dispatch')
# class OpteryMemberView(View):
#     """Class-based view for Optery member operations with enhanced error handling"""
    
#     def post(self, request):
#         """Create a new Optery member"""
#         try:
#             optery_base, optery_token = get_optery_config()
            
#             data = safe_json_parse(request.body, {})
#             if not data:
#                 return JsonResponse({
#                     "success": False,
#                     "error": "Invalid or empty JSON"
#                 }, status=400)
            
#             # Validate required fields
#             try:
#                 validate_required_fields(data, ['email', 'first_name', 'last_name', 'plan'])
#             except ValueError as e:
#                 return JsonResponse({
#                     "success": False,
#                     "error": str(e)
#                 }, status=400)
            
#             payload = {
#                 "email": str(data.get("email", "")),
#                 "first_name": str(data.get("first_name", "")),
#                 "last_name": str(data.get("last_name", "")),
#                 "middle_name": data.get("middle_name"),
#                 "city": data.get("city"),
#                 "country": data.get("country", "US"),
#                 "state": data.get("state"),
#                 "birthday_day": data.get("birthday_day"),
#                 "birthday_month": data.get("birthday_month"),
#                 "birthday_year": data.get("birthday_year"),
#                 "plan": data.get("plan"),
#                 "postpone_scan": data.get("postpone_scan", 45),
#                 "group_tag": data.get("group_tag"),
#                 "address_line1": data.get("address_line1"),
#                 "address_line2": data.get("address_line2"),
#                 "zipcode": data.get("zipcode")
#             }
            
#             # Remove None values
#             payload = {k: v for k, v in payload.items() if v is not None}
            
#             headers = {
#                 "Content-Type": "application/json",
#                 "Accept": "application/json",
#                 "Authorization": f"Bearer {optery_token}"
#             }
            
#             response = requests.post(
#                 f"{optery_base}v1/members",
#                 json=payload,
#                 headers=headers
#             )
            
#             response_data = safe_json_parse(response.text, {})
            
#             return JsonResponse({
#                 "success": response.status_code in [200, 201],
#                 "status_code": response.status_code,
#                 "data": response_data
#             }, status=response.status_code)
            
#         except ValueError as e:
#             if "configuration" in str(e):
#                 return JsonResponse({
#                     "success": False,
#                     "error": "Service configuration error"
#                 }, status=500)
#             return JsonResponse({
#                 "success": False,
#                 "error": "Invalid data format"
#             }, status=400)
            
#         except requests.exceptions.RequestException as e:
#             logger.error(f"API request failed: {str(e)}")
#             return JsonResponse({
#                 "success": False,
#                 "error": "Service temporarily unavailable"
#             }, status=503)
            
#         except Exception as e:
#             logger.error(f"Unexpected error in OpteryMemberView: {str(e)}", exc_info=True)
#             return JsonResponse({
#                 "success": False,
#                 "error": "Internal server error"
#             }, status=500)


class OpteryCombinedView(APIView):
    def get(self, request):
        try:
            optery_base, optery_token = get_optery_config()
            member_uuid = request.query_params.get("member_uuid")

            if not member_uuid:
                return Response({"error": "member_uuid is required"}, status=400)

            # Validate UUID format (basic check)
            if len(member_uuid) < 10:  # Basic UUID format check
                return Response({"error": "Invalid member_uuid format"}, status=400)

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {optery_token}"
            }

            # STEP 1: Get scans
            scan_url = f"{optery_base}v1/optouts/{member_uuid}/get-scans"
            try:
                scan_response = requests.get(scan_url, headers=headers)
            except requests.exceptions.RequestException as e:
                logger.error(f"Scan API request failed: {str(e)}")
                return Response({
                    "error": "Failed to connect to scan service"
                }, status=503)

            # Check HTTP status
            if scan_response.status_code != 200:
                logger.warning(f"Scan API returned status {scan_response.status_code}")
                return Response({
                    "error": f"Scan service returned error: {scan_response.status_code}",
                    "details": scan_response.text[:200]  # Limit detail length
                }, status=scan_response.status_code)
                
            scan_res = safe_json_parse(scan_response.text, {})

            # Handle API error responses
            if isinstance(scan_res, dict) and scan_res.get("error"):
                return Response({
                    "scan_api_error": scan_res.get("error"),
                    "raw": scan_res
                }, status=400)
                
            if not isinstance(scan_res, list):
                return Response({
                    "scan_api_error": "Invalid scan response format",
                    "received_type": type(scan_res).__name__
                }, status=400)

            # Collect scan IDs safely
            scan_ids = []
            for item in scan_res:
                if isinstance(item, dict) and item.get("scan_id"):
                    scan_ids.append(str(item.get("scan_id")))

            # If no scan IDs found
            if not scan_ids:
                return Response({
                    "message": "No scans found for this member",
                    "member_uuid": member_uuid,
                    "scans": scan_res
                }, status=200)

            screenshots = []

            for scan_id in scan_ids:
                ss_url = f"{optery_base}v1/optouts/{member_uuid}/get-screenshots-by-scan/{scan_id}"
                try:
                    ss_response = requests.get(ss_url, headers=headers)
                    if ss_response.status_code == 200:
                        ss_res = safe_json_parse(ss_response.text, {})
                    else:
                        ss_res = {"error": f"API returned {ss_response.status_code}"}
                except requests.exceptions.RequestException as e:
                    logger.error(f"Screenshot API request failed for scan {scan_id}: {str(e)}")
                    ss_res = {"error": "Failed to fetch screenshots"}

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
                    logger.error(f"Failed to save history for scan {scan_id}: {str(e)}")

            return Response({
                "member_uuid": member_uuid,
                "scans": scan_res,
                "screenshots": screenshots,
                "message": "Data fetched successfully"
            })

        except ValueError as e:
            if "configuration" in str(e):
                return Response({"error": "Service configuration error"}, status=500)
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in OpteryCombinedView: {str(e)}", exc_info=True)
            return Response({"error": "Internal server error"}, status=500)
class OpteryHistoryListView(APIView):

    def get(self, request):
        try:
            member_uuid = request.query_params.get("member_uuid")

            if not member_uuid:
                return Response({"error": "member_uuid is required"}, status=400)

            # Proper UUID validation
            try:
                uuid_obj = uuid.UUID(member_uuid)
            except ValueError:
                return Response({"error": "Invalid member_uuid format"}, status=400)

            histories = OpteryScanHistory.objects.filter(
                member_uuid=member_uuid
            ).order_by("-created_at")

            data = [
                {
                    "id": h.id,
                    "member_uuid": h.member_uuid,
                    "scan_id": h.scan_id,
                    "raw_scan_data": h.raw_scan_data,
                    "raw_screenshot_data": h.raw_screenshot_data,
                    "created_at": h.created_at,
                }
                for h in histories
            ]

            return Response({
                "success": True,
                "total": len(data),
                "history": data
            })

        except Exception as e:
            logger.error(f"Error in OpteryHistoryListView: {str(e)}", exc_info=True)
            return Response({"error": "Internal server error"}, status=500)




class CustomRemovalListView(APIView):
    def get(self, request):
        try:
            optery_base, optery_token = get_optery_config()
            
            # Query parameter থেকে member_uuid নেওয়া
            member_uuid = request.query_params.get("member_uuid")
            
            # member_uuid না থাকলে error
            if not member_uuid:
                return Response({
                    "error": "member_uuid is required as query parameter"
                }, status=400)
            
            # UUID validation (optional but recommended)
            if len(member_uuid) < 10:
                return Response({
                    "error": "Invalid member_uuid format"
                }, status=400)

            url = f"{optery_base}v1/optouts/{member_uuid}/custom-removals"
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {optery_token}"
            }

            try:
                response = requests.get(url, headers=headers, timeout=30)
                response_data = safe_json_parse(response.text, {})
                return Response(response_data, status=response.status_code)
            except requests.exceptions.RequestException as e:
                logger.error(f"Custom removal list API failed: {str(e)}")
                return Response({"error": "Failed to fetch custom removals"}, status=503)

        except ValueError as e:
            if "configuration" in str(e):
                return Response({"error": "Service configuration error"}, status=500)
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in CustomRemovalListView: {str(e)}", exc_info=True)
            return Response({"error": "Internal server error"}, status=500)


class CustomRemovalCreateView(APIView):
    def post(self, request):
        try:
            optery_base, optery_token = get_optery_config()
            member_uuid = request.GET.get("member_uuid")

            if not member_uuid:
                return Response({"error": "member_uuid is required as query parameter"}, status=400)

            # Validate UUID format
            if len(member_uuid) < 10:
                return Response({"error": "Invalid member_uuid format"}, status=400)

            url = f"{optery_base}v1/optouts/{member_uuid}/custom-removals"

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

            # Validate file size (e.g., 10MB limit)
            if proof_file.size > 10 * 1024 * 1024:
                return Response({"error": "File size too large (max 10MB)"}, status=400)

            data = {
                "exposed_url": exposed_url,
                "search_engine_url": search_engine_url,
                "search_keywords": search_keywords,
                "additional_information": additional_information,
            }

            try:
                files = {
                    "proof_of_exposure": (
                        proof_file.name,
                        proof_file.read(),
                        proof_file.content_type
                    )
                }
            except Exception as e:
                logger.error(f"File processing error: {str(e)}")
                return Response({"error": "Failed to process file"}, status=400)

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {optery_token}",
            }

            try:
                api_res = requests.post(url, data=data, files=files, headers=headers, timeout=60)
                response_data = safe_json_parse(api_res.text, {})
                return Response(response_data, status=api_res.status_code)
            except requests.exceptions.Timeout:
                return Response({"error": "Request timeout"}, status=504)
            except requests.exceptions.RequestException as e:
                logger.error(f"Custom removal create API failed: {str(e)}")
                return Response({"error": "Failed to create custom removal"}, status=503)

        except ValueError as e:
            if "configuration" in str(e):
                return Response({"error": "Service configuration error"}, status=500)
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in CustomRemovalCreateView: {str(e)}", exc_info=True)
            return Response({"error": "Internal server error"}, status=500)
        



from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import OpteryMember
from .serializers import OpteryMemberSerializer
import uuid

@api_view(['GET'])
def get_optery_member_by_uuid(request, uuid_str):
    """
    UUID অনুযায়ী OpteryMember এর ডেটা রিটার্ন করে
    """
    try:
        # UUID validation
        member_uuid = uuid.UUID(uuid_str)
    except ValueError:
        return Response(
            {"error": "Invalid UUID format"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get member or return 404
    member = get_object_or_404(OpteryMember, uuid=member_uuid)
    
    # Serialize the data
    serializer = OpteryMemberSerializer(member)
    print("Serialized Data:", serializer.data)  # Debugging line
    return Response({
        "success": True,
        "data": serializer.data
    }, status=status.HTTP_200_OK)