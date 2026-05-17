"""
Tests for MOSIP app.
"""

import json

from django.test import TestCase, Client
from django.contrib.auth.models import User
from mosip_auth_sdk.models import DemographicsModel
from rest_framework.test import APITestCase, APIClient
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

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

def generate_access_token(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class MOSIPAPITestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="testuser",
            password="password123"
        )

        self.access_token = generate_access_token(self.user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

    def test_client_ping(self):
        response = self.client.get("/api/mosip/ping/")
        
        self.assertEqual(response.status_code, 200)
    
    def test_factory_ping(self):
        self.access_token = generate_access_token(self.user)

        request = self.factory.get(
            "/api/mosip/ping/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        response = mosip_views.ping(request)
        
        assert response.status_code==200
    
    def test_client_auth_via_demographics(self):
        response = self.client.post(
            "/api/auth/demo/",
            {
                "uid" : sample_data["individual_id"],
                "name" : sample_data["name"][0]["value"]
            },
            format="json"
        )

        print(response.__dict__)

        self.assertEqual(response.status_code, 200)

    # def test_auth_via_demographics(self):
    #     request = self.factory.post(
    #         "/api/auth/demo/",
    #         {
    #             "uid" : sample_data["individual_id"],
    #             "name" : sample_data["name"][0]["value"]
    #         },
    #         format="json"
    #     )
    #     request.user = self.user

    #     response = mosip_views.auth_via_demographics(request)

    #     assert response.status_code==200
    
    # def test_auth_start_otp(self):
    #     self.client.login(username="testuser", password="password123")
    #     request = self.factory.post(
    #         "/api/auth/otp/start/",
    #         {
    #             "uid" : sample_data["individual_id"],
    #             "use_phone" : True
    #         },
    #         format="json"
    #     )
    #     request.user = self.user

    #     response = mosip_views.auth_start_otp(request)

    #     assert response.status_code==200

    # def test_auth_via_otp(self):
    #     self.client.login(username="testuser", password="password123")
    #     request = self.factory.post(
    #         "/api/auth/otp/start/",
    #         {
    #             "uid" : sample_data["individual_id"],
    #             "use_phone" : True
    #         },
    #         format="json"
    #     )
    #     request.user = self.user

    #     response = mosip_views.auth_start_otp(request)

    #     assert response.status_code==200

    #     content = json.loads(response.content)

    #     request = self.factory.post(
    #         "/api/auth/otp/verify/",
    #         {
    #             "uid" : sample_data["individual_id"],
    #             "txn_id" : content["txn_id"],
    #             "otp" : "111111"
    #         },
    #         format="json"
    #     )
    #     request.user = self.user

    #     response = mosip_views.auth_via_otp(request)

    #     assert response.status_code==200

    # def test_kyc_via_demographics(self):
    #     self.client.login(username="testuser", password="password123")
    #     request = self.factory.post(
    #         "/api/kyc/demo/",
    #         {
    #             "uid" : sample_data["individual_id"],
    #             "name" : sample_data["name"][0]["value"]
    #         },
    #         format="json"
    #     )
    #     request.user = self.user

    #     response = mosip_views.kyc_via_demographics(request)

    #     assert response.status_code==200

    # def test_kyc_start_otp(self):
    #     self.client.login(username="testuser", password="password123")
    #     request = self.factory.post(
    #         "/api/kyc/otp/start/",
    #         {
    #             "uid" : sample_data["individual_id"],
    #             "use_phone" : True
    #         },
    #         format="json"
    #     )
    #     request.user = self.user

    #     response = mosip_views.kyc_start_otp(request)

    #     assert response.status_code==200

    # def test_kyc_via_otp(self):
    #     self.client.login(username="testuser", password="password123")
    #     request = self.factory.post(
    #         "/api/kyc/otp/start/",
    #         {
    #             "uid" : sample_data["individual_id"],
    #             "use_phone" : True
    #         },
    #         format="json"
    #     )
    #     request.user = self.user

    #     response = mosip_views.kyc_start_otp(request)

    #     assert response.status_code==200

    #     content = json.loads(response.content)

    #     request = self.factory.post(
    #         "/api/kyc/otp/verify/",
    #         {
    #             "uid" : sample_data["individual_id"],
    #             "txn_id" : content["txn_id"],
    #             "otp" : "111111"
    #         },
    #         format="json"
    #     )
    #     request.user = self.user

    #     response = mosip_views.kyc_via_otp(request)

    #     assert response.status_code==200
