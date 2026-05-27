"""
Tests for MOSIP app.
"""


from django.test import TestCase
from mosip_auth_sdk.models import DemographicsModel
import requests

from .models import MOSIPKYCResponse, MOSIPAuthResponse, _to_demographic_data


# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=trailing-whitespace


# sample_data = {
#     "name" : [{
#         "language" : "eng",
#         "value" : "Mañuel Luis y Molina Quezon"
#     }],
#     "dob" : "1878/08/19",
#     "individual_id": "2092578314",
#     "individual_id_type": "UIN",
# }

sample_data = {
    "name" : [{
        "language" : "eng",
        "value" : "X Æ A-12 Boucher Musk"
    }],
    "dob" : "2020/05/01",
    "individual_id": "2184175105",
    "individual_id_type": "UIN",
}


class ToDemographicTestCase(TestCase):
    def test_name_to_demographic(self):
        self.assertEqual(
            _to_demographic_data(name=sample_data["name"][0]["value"]),
            DemographicsModel(name=sample_data["name"]),
            "DemographicsModel Test Name (English)"
        )

    def test_name_lang_to_demographic(self):
        self.assertEqual(
            _to_demographic_data(name_eng=sample_data["name"][0]["value"]),
            DemographicsModel(name=sample_data["name"]),
            "DemographicsModel Test Name (English)"
        )
    
    def test_dob_to_demographic(self):
        self.assertEqual(
            _to_demographic_data(dob=sample_data["dob"]),
            DemographicsModel(dob=sample_data["dob"]),
            "DemographicsModel Test DOB"
        )

    def test_dob_wrong_format_to_demographic(self):
        self.assertNotEqual(
            _to_demographic_data(dob=sample_data["dob"].replace("/", "-")),
            DemographicsModel(dob=sample_data["dob"].replace("/", "-")),
            "DemographicsModel Test Incorrect format DOB"
        )


class MOSIPKYCTestCase(TestCase):
    def test_kyc_via_demographics(self):
        request = requests.get(
            "https://api-internal.pdec.mosip.net",
            timeout=60
        )

        self.assertTrue(request.ok,
                        "Failed to connect to MOSIP Server.")

        response = MOSIPKYCResponse.from_demographics(
            uid=sample_data.get("individual_id"),
            name=sample_data.get("name", {})[0].get("value"),
            dob=sample_data.get("dob")
        )

        self.assertEqual(response.error_messages, [])
        self.assertTrue(response.user)
    
    def test_auth_via_demographics(self):
        request = requests.get(
            "https://api-internal.pdec.mosip.net",
            timeout=60
        )

        self.assertTrue(request.ok,
                        "Failed to connect to MOSIP Server.")

        response = MOSIPAuthResponse.from_demographics(
            uid=sample_data.get("individual_id"),
            name=sample_data.get("name", {})[0].get("value"),
            dob=sample_data.get("dob")
        )

        self.assertTrue(response.status)
