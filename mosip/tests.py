"""
Tests for MOSIP app.
"""


from mosip_auth_sdk.models import DemographicsModel

from django.test import TestCase
from .models import MOSIPCollabUser, to_demographic_data


sample_data = {
    "name": [{
        "language": "eng",
        "value":    "James Rodrigious"  
    }],
    "dob": "1992/04/29",
    "individual_id": "2047631038",
    "individual_id_type": "UIN",
}


class ToDemographicTestCase(TestCase):      # pylint: disable=missing-class-docstring
    def test_name_to_demographic(self):     # pylint: disable=missing-function-docstring
        self.assertEqual(
            to_demographic_data(name=sample_data["name"][0]["value"]),
            DemographicsModel(name=sample_data["name"]),
            "DemographicsModel Test Name (English)"
        )

        self.assertEqual(
            to_demographic_data(name=sample_data["name"][0]["value"]),
            DemographicsModel(name=sample_data["name"]),
            "DemographicsModel Test Name (English)"
        )
    
    def test_dob_to_demographic(self):      # pylint: disable=missing-function-docstring
        self.assertEqual(
            to_demographic_data(dob=sample_data["dob"]),
            DemographicsModel(dob=sample_data["dob"]),
            "DemographicsModel Test DOB"
        )

        self.assertNotEqual(
            to_demographic_data(dob=sample_data["dob"].replace("/", "-")),
            DemographicsModel(dob=sample_data["dob"].replace("/", "-")),
            "DemographicsModel Test Incorrect format DOB"
        )


