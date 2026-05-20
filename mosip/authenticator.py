"""
Authenticator Manager for MOSIP.
"""
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from dynaconf import Dynaconf

from mosip_auth_sdk import MOSIPAuthenticator

# pylint: disable=trailing-whitespace

@dataclass
class MOSIPAuthManager:
    """Authenticator manager for `MOSIPAuthenticator`.

    Raises:
        RuntimeError: `MOSIPAuthenticator` failed to initialize.

    Returns:
        MOSIPAuthenticator: Authenticator for MOSIP transactions.
    """
    _authenticator : Optional[MOSIPAuthenticator] = None
    _initialized : bool = False

    def get_authenticator(self) -> Optional[MOSIPAuthenticator] :
        """Initializes and fetches the `MOSIPAuthenticator`.

        Raises:
            RuntimeError: `MOSIPAuthenticator` failed to initialize.

        Returns:
            Optional[MOSIPAuthenticator]: Authenticator for MOSIP transactions, \
                or None if failed to initialize.
        """
        if self._initialized:
            if self._authenticator:
                return self._authenticator
            else:
                raise RuntimeError("MOSIP Authenticator failed to initialize.")
        
        try:
            config = Dynaconf(settings_files=[settings.CONFIG_MOSIP_SETTINGS], environments=False)
            self._authenticator = MOSIPAuthenticator(config=config)
        except Exception as err:
            print(f"Failed to initialized MOSIPAuthenticator: {err}")
            self._authenticator = None
        self._initialized = True

        return self._authenticator
