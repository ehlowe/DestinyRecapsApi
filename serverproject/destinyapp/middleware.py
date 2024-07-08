import os
import asyncio
from asgiref.sync import iscoroutinefunction

from django.http import JsonResponse
from django.utils.decorators import sync_and_async_middleware


# get the passcode
passcode=os.environ.get("req_pass","")

# Password middleware
@sync_and_async_middleware
def password_checker(get_response):
    if iscoroutinefunction(get_response):
        async def middleware(request):
            if passcode!=request.GET.get("mra"):
                return JsonResponse({"response":""})
            else:
                response = await get_response(request)
                return response
    else:
        def middleware(request):
            if passcode!=request.GET.get("mra"):
                return JsonResponse({"response":""})
            else:
                response = get_response(request)
                return response

    return middleware








print("MIddleware")


from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)

class AsyncErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        print("USING MIDDLEWARE")

    async def __call__(self, request):
        print("CALL MADE")
        try:
            response = await self.get_response(request)
            return response
        except Exception as e:
            return await self.handle_exception(e)

    async def handle_exception(self, exception):
        print("Exception: ",exception)

        if isinstance(exception, ValidationError):
            return JsonResponse({'error': 'Validation Error', 'details': exception.message_dict}, status=400)
        elif isinstance(exception, IntegrityError):
            return JsonResponse({'error': 'Database Integrity Error', 'details': str(exception)}, status=400)
        else:
            # Log the exception
            logger.exception('Unhandled exception occurred')
            # Return a generic error response
            return JsonResponse({'error': 'Internal Server Error'}, status=500)