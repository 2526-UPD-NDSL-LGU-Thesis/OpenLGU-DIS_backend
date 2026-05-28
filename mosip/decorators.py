""" 
MOSIP decorators.
"""


from functools import wraps
from rest_framework.response import Response
from rest_framework import status
import requests

from .exceptions import DRFErrors


def require_mosip(url="https://api-internal.pdec.mosip.net", timeout=120):
    """Checks if MOSIP server is running."""
    def decorator(view_method):

        @wraps(view_method)
        def wrapper(self, request, *args, **kwargs):

            try:
                response = requests.get(url, timeout=timeout)

                if not response.ok:
                    return Response(
                        {
                            "error"  : DRFErrors.MOSIPConnectionFailed,
                            "details": "Failed to connect to MOSIP servers."
                        },
                        status=status.HTTP_503_SERVICE_UNAVAILABLE
                    )

            except requests.RequestException as err:
                return Response(
                    {
                        "error"  : DRFErrors.MOSIPConnectionFailed,
                        "details": str(err)
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            return view_method(self, request, *args, **kwargs)

        return wrapper

    return decorator
