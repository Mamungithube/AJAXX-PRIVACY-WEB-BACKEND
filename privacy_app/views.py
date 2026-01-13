import os
import json
import logging
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
import requests
from celery.result import AsyncResult
from .models import OpteryScanHistory, OpteryMember
from .serializers import OpteryMemberSerializer
from .tasks import fetch_optery_scans_background

logger = logging.getLogger(__name__)


"""--------------------Utility functions--------------------"""

def get_optery_config():
    """Safely get Optery configuration from environment with validation"""
    base_url = settings.OPTERY_BASE_URL
    api_token = settings.OPTERY_API_KEY
    
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


"""--------------------Create Optery Member--------------------"""

@method_decorator(csrf_exempt, name='dispatch')
class CreateOpteryMember(APIView):
    def post(self, request):
        # Validate input data
        serializer = OpteryMemberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check API configuration
        try:
            optery_base, optery_token = get_optery_config()
        except ValueError:
            return Response({
                "success": False,
                "error": "Service configuration error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Prepare Optery API request
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {optery_token}"
        }

        api_url = optery_base.rstrip('/') + '/v1/members'

        try:
            # Call Optery API
            optery_response = requests.post(
                api_url,
                headers=headers,
                json=serializer.validated_data,
                timeout=30
            )

            response_data = optery_response.json()
            is_success = optery_response.status_code in [200, 201]

            # Only save to database if API call was successful
            if is_success:
                OpteryMember.objects.create(
                    uuid=response_data.get("uuid"),
                    email=serializer.validated_data["email"],
                    first_name=serializer.validated_data["first_name"],
                    last_name=serializer.validated_data["last_name"],
                    middle_name=serializer.validated_data.get("middle_name"),
                    city=serializer.validated_data.get("city"),
                    country=serializer.validated_data.get("country", "US"),
                    state=serializer.validated_data.get("state"),
                    birthday_day=serializer.validated_data.get("birthday_day"),
                    birthday_month=serializer.validated_data.get("birthday_month"),
                    birthday_year=serializer.validated_data.get("birthday_year"),
                    plan=serializer.validated_data["plan"],
                    postpone_scan=serializer.validated_data.get("postpone_scan", 45),
                    group_tag=serializer.validated_data.get("group_tag"),
                    address_line1=serializer.validated_data.get("address_line1"),
                    address_line2=serializer.validated_data.get("address_line2"),
                    zipcode=serializer.validated_data.get("zipcode"),
                    optery_response=response_data,
                    status_code=optery_response.status_code,
                    is_success=True
                )

            return Response({
                "success": is_success,
                "status_code": optery_response.status_code,
                "optery_response": response_data,
                "data": response_data
            }, status=optery_response.status_code)

        except Exception as e:
            logger.error(f"Create member error: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


"""--------------------Optery Combined View with Background Task--------------------"""

class OpteryCombinedView(APIView):
    """
    GET with task_id: Check task status and get result
    POST: Start background task to fetch scans
    """
    
    def post(self, request):
        """Start background task - Returns task_id immediately"""
        try:
            member_uuid = request.data.get("member_uuid")
            email = request.data.get("email")
            
            if not member_uuid:
                return Response({"error": "member_uuid is required"}, status=400)

            # Email validation
            if email and ("@" not in email or "." not in email):
                return Response({"error": "Invalid email format"}, status=400)

            # Start background task
            task = fetch_optery_scans_background.delay(member_uuid, email)
            
            return Response({
                "status": "processing",
                "task_id": task.id,
                "message": "Request submitted successfully. Use GET with task_id to check status.",
                "member_uuid": member_uuid,
                "email": email if email else "Not provided"
            }, status=202)  # 202 Accepted

        except Exception as e:
            logger.error(f"Error starting background task: {str(e)}", exc_info=True)
            return Response({
                "error": "Failed to start background task",
                "details": str(e)
            }, status=500)

    def get(self, request):
        """
        Check task status or get final result
        Query params: task_id (optional), member_uuid (for backwards compatibility)
        """
        task_id = request.query_params.get("task_id")
        member_uuid = request.query_params.get("member_uuid")
        email = request.query_params.get("email")
        
        # If task_id provided, check task status
        if task_id:
            try:
                task_result = AsyncResult(task_id)
                
                if task_result.ready():
                    if task_result.successful():
                        result = task_result.result
                        # Return exact same structure as old API
                        return Response(result, status=200)
                    else:
                        return Response({
                            "status": "failed",
                            "error": str(task_result.result),
                            "task_id": task_id
                        }, status=500)
                else:
                    # Task still processing
                    return Response({
                        "status": "processing",
                        "task_id": task_id,
                        "message": "Task is still running. Please check again in a few seconds."
                    }, status=202)

            except Exception as e:
                logger.error(f"Error checking task status: {str(e)}", exc_info=True)
                return Response({
                    "error": "Failed to check task status",
                    "details": str(e)
                }, status=500)
        
        # Backwards compatibility: If no task_id, start task immediately (old behavior)
        elif member_uuid:
            logger.warning("Using deprecated direct GET call. Please use POST to start task.")
            task = fetch_optery_scans_background.delay(member_uuid, email)
            return Response({
                "status": "processing",
                "task_id": task.id,
                "message": "Task started. Use task_id to check status.",
                "member_uuid": member_uuid
            }, status=202)
        
        else:
            return Response({
                "error": "Either task_id or member_uuid is required"
            }, status=400)


"""--------------------Optery History List View--------------------"""

class OpteryHistoryListView(APIView):
    def get(self, request, email_str):
        try:
            if not email_str:
                return Response({"error": "email is required"}, status=400)

            histories = OpteryScanHistory.objects.filter(
                email=email_str
            ).order_by("-created_at")

            data = [
                {
                    "id": h.id,
                    "email": h.email,
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


"""--------------------Custom Removal List View--------------------"""

class CustomRemovalListView(APIView):
    def get(self, request):
        try:
            optery_base, optery_token = get_optery_config()
            
            member_uuid = request.query_params.get("member_uuid")
            
            if not member_uuid:
                return Response({
                    "error": "member_uuid is required as query parameter"
                }, status=400)
            
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


"""--------------------Custom Removal Create View--------------------"""

class CustomRemovalCreateView(APIView):
    def post(self, request):
        try:
            optery_base, optery_token = get_optery_config()
            member_uuid = request.GET.get("member_uuid")

            if not member_uuid:
                return Response({"error": "member_uuid is required as query parameter"}, status=400)

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


"""--------------------Get Optery Member by Email--------------------"""

@api_view(['GET'])
def get_optery_member_by_email(request, email_str):
    members_queryset = OpteryMember.objects.filter(email__exact=email_str)

    if not members_queryset.exists():
        return Response(
            {"error": f"No OpteryMember found with email: {email_str}"},
            status=status.HTTP_404_NOT_FOUND
        )

    member = members_queryset.first()
    serializer = OpteryMemberSerializer(member)

    return Response({
        "success": True,
        "data": serializer.data
    }, status=status.HTTP_200_OK)