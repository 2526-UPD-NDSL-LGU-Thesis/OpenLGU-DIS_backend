"""
Tests for MOSIP app.
"""

import json

from django.test import TestCase
from mosip_auth_sdk.models import DemographicsModel
from rest_framework.test import APIRequestFactory

from .models import _to_demographic_data
from . import views as mosip_views

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=trailing-whitespace


sample_data = {
    "name": [{
        "language": "eng",
        "value": "James Rodrigious"  
    }],
    "dob": "1992/04/29",
    "individual_id": "2047631038",
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

# class MOSIPUserTestCase(TestCase):
#     def test_mosip_kyc(self):
#         self.assertEqual(
#             MOSIPUser
#         )


class MOSIPAPITestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_ping(self):
        request = self.factory.get("/mosip/ping/")

        response = mosip_views.ping(request)
        
        assert response.status_code==200

    def test_auth_via_demographics(self):
        request = self.factory.post(
            "/auth/demo/",
            {
                "uid" : sample_data["individual_id"],
                "name" : sample_data["name"][0]["value"]
            },
            format="json"
        )

        response = mosip_views.auth_via_demographics(request)

        assert response.status_code==200
    
    def test_auth_start_otp(self):
        request = self.factory.post(
            "/auth/otp/start/",
            {
                "uid" : sample_data["individual_id"],
                "use_phone" : True
            },
            format="json"
        )

        response = mosip_views.auth_start_otp(request)

        assert response.status_code==200

    def test_auth_via_otp(self):
        request = self.factory.post(
            "/auth/otp/start/",
            {
                "uid" : sample_data["individual_id"],
                "use_phone" : True
            },
            format="json"
        )

        response = mosip_views.auth_start_otp(request)

        assert response.status_code==200

        content = json.loads(response.content)

        request = self.factory.post(
            "/auth/otp/verify/",
            {
                "uid" : sample_data["individual_id"],
                "txn_id" : content["txn_id"],
                "otp" : "111111"
            },
            format="json"
        )

        response = mosip_views.auth_via_otp(request)

        assert response.status_code==200

    def test_kyc_via_demographics(self):
        request = self.factory.post(
            "/kyc/demo/",
            {
                "uid" : sample_data["individual_id"],
                "name" : sample_data["name"][0]["value"]
            },
            format="json"
        )

        response = mosip_views.kyc_via_demographics(request)

        assert response.status_code==200

    def test_kyc_start_otp(self):
        request = self.factory.post(
            "/kyc/otp/start/",
            {
                "uid" : sample_data["individual_id"],
                "use_phone" : True
            },
            format="json"
        )

        response = mosip_views.kyc_start_otp(request)

        assert response.status_code==200

    def test_kyc_via_otp(self):
        request = self.factory.post(
            "/kyc/otp/start/",
            {
                "uid" : sample_data["individual_id"],
                "use_phone" : True
            },
            format="json"
        )

        response = mosip_views.kyc_start_otp(request)

        assert response.status_code==200

        content = json.loads(response.content)

        request = self.factory.post(
            "/kyc/otp/verify/",
            {
                "uid" : sample_data["individual_id"],
                "txn_id" : content["txn_id"],
                "otp" : "111111"
            },
            format="json"
        )

        response = mosip_views.kyc_via_otp(request)

        assert response.status_code==200
