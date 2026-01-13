import logging
import requests
from celery import shared_task
from django.conf import settings
from .models import OpteryScanHistory
import concurrent.futures

logger = logging.getLogger(__name__)


def get_optery_config():
    """Get Optery configuration"""
    base_url = settings.OPTERY_BASE_URL
    api_token = settings.OPTERY_API_KEY
    
    if not base_url or not api_token:
        logger.error("Optery configuration missing")
        raise ValueError("Optery API configuration not found")
    
    if not base_url.endswith('/'):
        base_url += '/'
    
    return base_url, api_token


def safe_json_parse(text, default=None):
    """Safely parse JSON"""
    if not text or not text.strip():
        return default
    
    try:
        import json
        return json.loads(text)
    except Exception as e:
        logger.error(f"JSON parse error: {str(e)}")
        return default


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def fetch_optery_scans_background(self, member_uuid, email=None):
    """
    Background task to fetch Optery scans and screenshots
    Response structure same as before - frontend compatible
    """
    try:
        optery_base, optery_token = get_optery_config()
        
        # Ensure email is set to a non-null default to avoid DB NOT NULL errors
        email = email or 'Not provided'

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {optery_token}"
        }

        # STEP 1: Get scans with reasonable timeout for production
        scan_url = f"{optery_base}v1/optouts/{member_uuid}/get-scans"
        try:
            scan_response = requests.get(scan_url, headers=headers, timeout=30)
        except requests.exceptions.RequestException as e:
            logger.error(f"Scan API request failed: {str(e)}")
            return {
                "error": "Failed to connect to scan service",
                "member_uuid": member_uuid,
                "email": email if email else "Not provided"
            }

        if scan_response.status_code != 200:
            logger.warning(f"Scan API returned status {scan_response.status_code}")
            details = scan_response.text[:200]
            # Retry on server errors (5xx), treat client errors (4xx) as final
            if 500 <= scan_response.status_code < 600:
                raise Exception(f"Scan service error {scan_response.status_code}: {details}")
            return {
                "error": f"Scan service returned error: {scan_response.status_code}",
                "details": details,
                "member_uuid": member_uuid,
                "email": email
            }
        
        scan_res = safe_json_parse(scan_response.text, {})

        # Handle API error responses
        if isinstance(scan_res, dict) and scan_res.get("error"):
            return {
                "scan_api_error": scan_res.get("error"),
                "raw": scan_res,
                "member_uuid": member_uuid,
                "email": email if email else "Not provided"
            }
        
        if not isinstance(scan_res, list):
            return {
                "scan_api_error": "Invalid scan response format",
                "received_type": type(scan_res).__name__,
                "member_uuid": member_uuid,
                "email": email if email else "Not provided"
            }

        # Collect scan IDs
        scan_ids = []
        for item in scan_res:
            if isinstance(item, dict) and item.get("scan_id"):
                scan_ids.append(str(item.get("scan_id")))

        if not scan_ids:
            return {
                "message": "No scans found for this member",
                "member_uuid": member_uuid,
                "email": email if email else "Not provided",
                "scans": scan_res
            }

        # STEP 2: Parallel fetch screenshots
        def fetch_single_screenshot(scan_id):
            """Fetch screenshot for single scan"""
            ss_url = f"{optery_base}v1/optouts/{member_uuid}/get-screenshots-by-scan/{scan_id}"
            try:
                # shorter per-request timeout to keep task runtime bounded
                ss_response = requests.get(ss_url, headers=headers, timeout=30)
                if ss_response.status_code == 200:
                    ss_res = safe_json_parse(ss_response.text, {})
                else:
                    ss_res = {"error": f"API returned {ss_response.status_code}"}
            except requests.exceptions.RequestException as e:
                logger.error(f"Screenshot fetch failed for scan {scan_id}: {str(e)}")
                ss_res = {"error": "Failed to fetch screenshots"}

            # Save to database - if save fails raise to propagate failure
            try:
                OpteryScanHistory.objects.create(
                    member_uuid=member_uuid,
                    email=email,
                    scan_id=scan_id,
                    raw_scan_data=scan_res,
                    raw_screenshot_data=ss_res
                )
            except Exception as e:
                logger.error(f"DB save failed for scan {scan_id}: {str(e)}", exc_info=True)
                # Raising here will surface the exception to the ThreadPoolExecutor
                # and cause the main task to hit the outer except and retry/fail.
                raise

            return {
                "scan_id": scan_id,
                "screenshots": ss_res
            }

        # Parallel processing with ThreadPoolExecutor
        screenshots = []
        # reduced worker count to limit parallel outbound requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            screenshot_results = list(executor.map(fetch_single_screenshot, scan_ids))
        
        screenshots = screenshot_results

        # Return exact same structure as before
        return {
            "member_uuid": member_uuid,
            "email": email if email else "Not provided",
            "scans": scan_res,
            "screenshots": screenshots,
            "message": "Data fetched successfully"
        }

    except Exception as e:
        logger.error(f"Task failed for {member_uuid}: {str(e)}", exc_info=True)
        # Retry the task
        try:
            raise self.retry(exc=e, countdown=60)
        except self.MaxRetriesExceededError:
            return {
                "error": "Maximum retries exceeded",
                "details": str(e),
                "member_uuid": member_uuid
            }