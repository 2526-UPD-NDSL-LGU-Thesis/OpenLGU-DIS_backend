""" 
MOSIP decorators.
"""


from functools import wraps
from rest_framework.response import Response
from rest_framework import status
import requests

from .exceptions import DRFErrors


def require_mosip(
    urls=[
        "https://api.pdec.mosip.net/idauthentication/v1",
        "https://api-internal.pdec.mosip.net"
    ],
    timeout=60,
    require_all=False,
):
    """
    Checks connectivity against one or more MOSIP endpoints.

    Args:
        urls (list[str] | tuple[str]):
            URLs to test.

        require_all (bool):
            True  -> all URLs must be reachable
            False -> at least one URL must be reachable
    """

    if isinstance(urls, str):
        urls = [urls]

    def decorator(view_method):

        @wraps(view_method)
        def wrapper(*args, **kwargs):

            results = []

            for url in urls:

                try:
                    response = requests.get(url, timeout=timeout)

                    success = response.ok

                    results.append(
                        {
                            "url": url,
                            "ok": success,
                            "status_code": response.status_code,
                        }
                    )

                except requests.RequestException as err:

                    results.append(
                        {
                            "url": url,
                            "ok": False,
                            "error": str(err),
                        }
                    )

            reachable = [r for r in results if r["ok"]]

            passed = (
                len(reachable) == len(results)
                if require_all
                else len(reachable) > 0
            )

            if not passed:
                return Response(
                    {
                        "error": DRFErrors.MOSIPConnectionFailed,
                        "details": results,
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            return view_method(*args, **kwargs)

        return wrapper

    return decorator


def require_mosip_decoders(
    urls=[
        "https://api.pdec.mosip.net/idauthentication/v1",
        "https://api-internal.pdec.mosip.net"
    ],
    timeout=60,
    require_all=False,
):
    """
    Checks connectivity against one or more MOSIP endpoints.

    Args:
        urls (list[str] | tuple[str]):
            URLs to test.

        require_all (bool):
            True  -> all URLs must be reachable
            False -> at least one URL must be reachable
    """

    if isinstance(urls, str):
        urls = [urls]

    def decorator(view_method):

        @wraps(view_method)
        def wrapper(*args, **kwargs):

            results = []

            for url in urls:

                try:
                    response = requests.get(url, timeout=timeout)

                    success = response.ok

                    results.append(
                        {
                            "url": url,
                            "ok": success,
                            "status_code": response.status_code,
                        }
                    )

                except requests.RequestException as err:

                    results.append(
                        {
                            "url": url,
                            "ok": False,
                            "error": str(err),
                        }
                    )

            reachable = [r for r in results if r["ok"]]

            passed = (
                len(reachable) == len(results)
                if require_all
                else len(reachable) > 0
            )

            if not passed:
                raise ValueError("Failed to connect to MOSIP API.")

            return view_method(*args, **kwargs)

        return wrapper

    return decorator
