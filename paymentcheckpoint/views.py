import json
import logging
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from opaque_keys.edx.keys import UsageKey
from xmodule.modulestore.django import modulestore, get_module_for_student

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def mark_complete(request):
    """
    API endpoint for the WordPress plugin to mark a PaymentCheckpointXBlock as complete.

    Expected JSON body:
        {
            "username": "student_username",
            "usage_key": "block-v1:... (the usage key of the XBlock)"
        }

    The request must be authenticated with a valid JWT token (platform-level).
    No additional API key or token is required inside the XBlock.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    username = data.get('username')
    usage_key_str = data.get('usage_key')

    if not username or not usage_key_str:
        return JsonResponse({'error': 'Missing username or usage_key'}, status=400)

    # Validate usage key
    try:
        usage_key = UsageKey.from_string(usage_key_str)
    except Exception:
        return JsonResponse({'error': 'Invalid usage_key'}, status=400)

    # Verify user exists
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    # Load student-specific XBlock instance
    try:
        student_block = get_module_for_student(user, usage_key)
    except Exception as e:
        logger.exception("Failed to load XBlock for %s", usage_key)
        return JsonResponse({'error': 'Could not load student state'}, status=500)

    # Mark as complete
    if hasattr(student_block, 'complete'):
        student_block.complete = True
        student_block.save()

        # Update the completion service to trigger gating
        try:
            from completion.services import CompletionService
            CompletionService().set_completion(user, usage_key, 1.0)
        except ImportError:
            logger.warning('Completion service not available, skipping.')

        return JsonResponse({'status': 'ok'})
    else:
        return JsonResponse({'error': 'XBlock does not have a complete field'}, status=400)