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
    authenticator : Optional[MOSIPAuthenticator] = None
    initialized : bool = False

    def get_authenticator(self) -> Optional[MOSIPAuthenticator] :
        """Initializes and fetches the `MOSIPAuthenticator`.

        Raises:
            RuntimeError: `MOSIPAuthenticator` failed to initialize.

        Returns:
            Optional[MOSIPAuthenticator]: Authenticator for MOSIP transactions, \
                or None if failed to initialize.
        """
        if self.initialized:
            if self.authenticator:
                return self.authenticator
            else:
                raise RuntimeError("Authenticator not initialized.")
        
        try:
            config = Dynaconf(settings_files=[settings.CONFIG_MOSIP_SETTINGS], environments=False)
            self.authenticator = MOSIPAuthenticator(config=config)
        except Exception as err:
            print(f"Failed to initialized MOSIPAuthenticator: {err}")
            self.authenticator = None
        self.initialized = True

        return self.authenticator
