"""
QR code decoders for QR Manager.
"""

from dataclasses import asdict
from typing import Dict
from pycose.messages.sign1message import Sign1Message
import base45
import base64
import cbor2
import json
import zlib

from mosip.models import MOSIPAuthResponse
from mosip.decorators import require_mosip_decoders

from .main import pycose_verify_message
from .classes import QRDetails


# pylint: disable=missing-function-docstring
# pylint: disable=trailing-whitespace


def _to_base64_image(image_bytes : bytes) -> str :
    return base64.b64encode(image_bytes).decode()


@require_mosip_decoders()
def decode_philsys_temporary_qr(qr_code : str) -> Dict :
    # Generate 'None's
    issued_at = None
    issuer = None
    subject_biographic = None
    face_image = None
    gender = None
    best_fingers = None
    first_name = None
    last_name = None
    middle_name = None
    suffix_name = None
    date_of_birth = None
    pcn = None
    place_of_birth = None

    # Separate prefix
    prefix, content = qr_code[:4], qr_code[4:]

    # Decode payload
    try:
        b45_qr = base45.b45decode(content)
    except Exception as err:
        raise ValueError("QR code is not a valid base45 encoding.") from err

    try:
        signed_msg = Sign1Message.decode(b45_qr)
    except Exception as err:
        raise ValueError("Message is not a valid Sign1Message.") from err
    
    try:
        payload : Dict = cbor2.loads(signed_msg.payload)
    except Exception as err:
        raise ValueError("Payload is not a valid CBOR object.") from err
    
    # Cannot verify QR code, missing public keys for verification

    # Logging unused keys
    used_payload_keys = set()
    used_claim169_keys = set()
    used_sb_keys = set()

    # Standardize payload
    token_issuer = payload.get(1)
    used_payload_keys.add(1)

    token_issued_at = payload.get(6)
    used_payload_keys.add(6)

    token_confirmation = payload.get(8)
    used_payload_keys.add(8)

    token_claim169 : Dict = payload.get(169)
    used_payload_keys.add(169)
    if token_claim169:
        issued_at = token_claim169.get("d")
        used_claim169_keys.add("d")

        issuer = token_claim169.get("i")
        used_claim169_keys.add("i")

        subject_biographic  : Dict = token_claim169.get("sb")
        used_claim169_keys.add("sb")

        face_image = _to_base64_image(token_claim169.get("img"))
        used_claim169_keys.add("img")

        if subject_biographic:
            gender = subject_biographic.get("s")
            used_sb_keys.add("s")

            best_fingers = subject_biographic.get("BF").strip("[]").split(",")
            used_sb_keys.add("BF")

            first_name = subject_biographic.get("fn")
            used_sb_keys.add("fn")

            last_name = subject_biographic.get("ln")
            used_sb_keys.add("ln")

            middle_name = subject_biographic.get("mn")
            used_sb_keys.add("mn")

            suffix_name = subject_biographic.get("sf")
            used_sb_keys.add("sf")

            date_of_birth = subject_biographic.get("DOB")
            used_sb_keys.add("DOB")

            pcn = subject_biographic.get("PCN")
            used_sb_keys.add("PCN")

            place_of_birth = subject_biographic.get("POB")
            used_sb_keys.add("POB")
    
    # MOSIP Auth
    full_name = (
        f"{first_name} {middle_name} {last_name} {suffix_name}" if suffix_name
        else f"{first_name} {middle_name} {last_name}"
    )
    mosip_response = MOSIPAuthResponse.from_demographics(uid=pcn, name=full_name,
                                                         dob=date_of_birth, gender=gender)
    
    if mosip_response.errors:
        raise ValueError(f"Encountered errors during MOSIP Auth: {mosip_response.errors}")

    if not mosip_response.status:
        raise ValueError("MOSIP Auth failed.")
    
    # Getting unused headers
    unused_payload_keys = set(payload.keys()) - used_payload_keys
    unused_claim169_keys = set(token_claim169.keys()) - used_claim169_keys
    unused_sb_keys = set(subject_biographic.keys()) - used_sb_keys

    if unused_payload_keys:
        print("Unused payload keys: ", unused_payload_keys)
    
    if unused_claim169_keys:
        print("Unused claim169 keys: ", unused_claim169_keys)
    
    if unused_sb_keys:
        print("Unused sb keys: ", unused_sb_keys)

    id_details = QRDetails(
        token_issuer=token_issuer,
        token_issued_at=token_issued_at,
        token_confirmation=token_confirmation,
        issuer=issuer,
        issued_at=issued_at,
        pcn=pcn,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        suffix_name=suffix_name,
        gender=gender,
        date_of_birth=date_of_birth,
        place_of_birth=place_of_birth,
        best_fingers=best_fingers,
        face_image=face_image
    )
    
    return asdict(id_details)


@require_mosip_decoders()
def decode_philsys_physical_qr(qr_code : str) -> Dict :
    # Generate 'None's
    best_fingers = None
    date_of_birth = None
    pcn = None
    place_of_birth = None
    suffix_name = None
    first_name = None
    last_name = None
    middle_name = None
    gender = None
    
    # Logging unused keys
    used_payload_keys = set()
    used_subject_keys = set()

    # Standardize payload
    payload : Dict = json.loads(qr_code)

    issued_at = payload.get("DateIssued")
    used_payload_keys.add("DateIssued")

    issuer = payload.get("Issuer")
    used_payload_keys.add("Issuer")

    algorithm = payload.get("alg")
    used_payload_keys.add("alg")

    signature = payload.get("signature")
    used_payload_keys.add("signature")

    subject : Dict = payload.get("subject")
    used_payload_keys.add("subject")
    
    if subject:
        best_fingers = subject.get("BF").strip("[]").split(",")
        used_subject_keys.add("BF")

        date_of_birth = subject.get("DOB")
        used_subject_keys.add("DOB")

        pcn = subject.get("PCN")
        used_subject_keys.add("PCN")

        place_of_birth = subject.get("POB")
        used_subject_keys.add("POB")

        suffix_name = subject.get("Suffix")
        used_subject_keys.add("Suffix")

        first_name = subject.get("fName")
        used_subject_keys.add("fName")

        last_name = subject.get("lName")
        used_subject_keys.add("lName")

        middle_name = subject.get("mName")
        used_subject_keys.add("mName")

        gender = subject.get("sex")
        used_subject_keys.add("sex")
    
    # MOSIP Auth
    full_name = (
        f"{first_name} {middle_name} {last_name} {suffix_name}" if suffix_name
        else f"{first_name} {middle_name} {last_name}"
    )
    mosip_response = MOSIPAuthResponse.from_demographics(uid=pcn, name=full_name,
                                                         dob=date_of_birth, gender=gender)
    
    if mosip_response.errors:
        raise ValueError(f"Encountered errors during MOSIP Auth: {mosip_response.errors}")

    if not mosip_response.status:
        raise ValueError("MOSIP Auth failed.")
    
    # Getting unused headers
    unused_payload_keys = set(payload.keys()) - used_payload_keys
    unused_subject_keys = set(subject.keys()) - used_subject_keys

    if unused_payload_keys:
        print("Unused payload keys: ", unused_payload_keys)
    
    if unused_subject_keys:
        print("Unused subject keys: ", unused_subject_keys)
    
    id_details = QRDetails(
        issued_at=issued_at,
        issuer=issuer,
        algorithm=algorithm,
        signature=signature,
        best_fingers=best_fingers,
        date_of_birth=date_of_birth,
        pcn=pcn,
        place_of_birth=place_of_birth,
        suffix_name=suffix_name,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        gender=gender
    )

    return asdict(id_details)


def decode_egovph_front_qr(qr_code : str) -> Dict :
    payload = json.loads(qr_code)

    id_details = QRDetails(pcn=payload)

    return asdict(id_details)


def decode_egovph_back_qr(qr_code : str) -> Dict : 
    # Generate 'None's
    date_of_birth = None
    best_fingers = None
    bloodtype = None
    issued_at = None
    egov_digital_id = None
    issuer = None
    marital_status = None
    first_name = None
    last_name = None
    middle_name = None
    suffix_name = None
    face_image = None
    pcn = None
    place_of_birth = None
    gender = None
    signature = None

    # Logging unused keys
    used_payload_keys = set()

    # Standardize payload
    payload : Dict = json.loads(qr_code)
    
    version = payload.get("v")
    used_payload_keys.add("v")

    if version == "2.0":
        date_of_birth = payload.get("bd")
        used_payload_keys.add("bd")

        best_fingers = payload.get("bf")
        used_payload_keys.add("bf")

        bloodtype = payload.get("bt")
        used_payload_keys.add("bt")

        issued_at = payload.get("iat")
        used_payload_keys.add("iat")

        egov_digital_id = payload.get("id")
        used_payload_keys.add("id")

        issuer = payload.get("iss")
        used_payload_keys.add("iss")

        marital_status = payload.get("ms")
        used_payload_keys.add("ms")

        first_name = payload.get("n_f")
        used_payload_keys.add("n_f")

        last_name = payload.get("n_l")
        used_payload_keys.add("n_l")

        middle_name = payload.get("n_m")
        used_payload_keys.add("n_m")

        suffix_name = payload.get("n_s")
        used_payload_keys.add("n_s")

        face_image = payload.get("p")
        used_payload_keys.add("p")

        pcn = payload.get("pcn")
        used_payload_keys.add("pcn")

        place_of_birth = payload.get("pob")
        used_payload_keys.add("pob")

        gender = payload.get("s")
        used_payload_keys.add("s")

        signature = payload.get("z")
        used_payload_keys.add("z")
    
    else:
        raise ValueError(
            f"eGovPH Back QR version {version} is not supported with curret QR code reader."
        )

    # Getting unused headers
    unused_payload_keys = set(payload.keys()) - used_payload_keys

    if unused_payload_keys:
        print("Unused payload keys: ", unused_payload_keys)
    
    id_details = QRDetails(
        date_of_birth=date_of_birth,
        best_fingers=best_fingers,
        bloodtype=bloodtype,
        issued_at=issued_at,
        egov_digital_id=egov_digital_id,
        issuer=issuer,
        marital_status=marital_status,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        suffix_name=suffix_name,
        face_image=face_image,
        pcn=pcn,
        place_of_birth=place_of_birth,
        gender=gender,
        version=version,
        signature=signature
    )
    
    return asdict(id_details)


def decode_openlgu_qr(qr_code : str) -> Dict :
    # Generate 'None's
    pcn = None
    version = None
    language = None
    full_name = None
    first_name = None
    middle_name = None
    last_name = None
    date_of_birth = None
    gender = None
    address = None
    email_id = None
    phone_number = None
    nationality = None
    marital_status = None
    # guardian = None
    # binary_image = None
    # binary_image_format = None
    best_fingers = None
    # full_name_secondary = None
    # language_secondary = None
    # location_code = None
    # legal_status = None
    issuing_country = None
    # 24 - 49 : For future - For Demographic Data attributes
    # right_thumb = None
    # right_pointer_finger = None
    # right_middle_finger = None
    # right_ring_finger = None
    # right_little_finger = None
    # left_thumb = None
    # left_pointer_finger = None
    # left_middle_finger = None
    # left_ring_finger = None
    # left_little_finger = None
    # right_iris = None
    # left_iris = None
    face_image = None
    # right_palm_print = None
    # left_palm_print = None
    # voice = None
    # 66 - 74 : For future - For Biometrics Data attributes
    # 75 - 99 : For future - For any other data
    uin = None
    
    # Decode payload
    try:
        b45_qr = base45.b45decode(qr_code)
    except Exception as err:
        raise ValueError("QR code is not a valid base45 encoding.") from err

    try:
        decompressed_qr = zlib.decompress(b45_qr)
    except Exception as err:
        raise ValueError("Content is not decompressed using zlib.") from err

    try:
        payload = pycose_verify_message(decompressed_qr)
    except Exception as err:
        raise ValueError(f"Failed to verify QR code: {err}") from err

    # Logging unused keys
    used_payload_keys = set()
    used_claim169_keys = set()

    # Standardize payload
    token_issuer = payload.get(1)
    used_payload_keys.add(1)

    token_issued_at = payload.get(6)
    used_payload_keys.add(6)

    token_claim169 : Dict = payload.get(169)
    used_payload_keys.add(169)

    if token_claim169:
        pcn = token_claim169.get(1)
        used_claim169_keys.add(1)

        version = token_claim169.get(2)
        used_claim169_keys.add(2)

        if version == "1.2.1" or version is None:
            #TODO: perform ISO 639-3 languange code check
            language = token_claim169.get(3)
            used_claim169_keys.add(3)

            full_name = token_claim169.get(4)
            used_claim169_keys.add(4)

            first_name = token_claim169.get(5)
            used_claim169_keys.add(5)

            middle_name = token_claim169.get(6)
            used_claim169_keys.add(6)

            last_name = token_claim169.get(7)
            used_claim169_keys.add(7)

            date_of_birth = token_claim169.get(8)
            used_claim169_keys.add(8)

            _gender_value = token_claim169.get(9)
            gender = (
                "Male" if _gender_value == 1
                else "Female" if _gender_value == 2
                else "Others" if _gender_value == 3
                else "Unknown"
            )
            used_claim169_keys.add(9)
            
            address = token_claim169.get(10)
            used_claim169_keys.add(10)

            email_id = token_claim169.get(11)
            used_claim169_keys.add(11)

            phone_number = token_claim169.get(12)
            used_claim169_keys.add(12)

            #TODO: Perform ISO 3166-1 country code check
            nationality = token_claim169.get(13)
            used_claim169_keys.add(13)

            _marital_status_value = token_claim169.get(14)
            marital_status = (
                "Unmarried" if _marital_status_value == 1
                else "Married" if _marital_status_value == 2
                else "Divorced" if _marital_status_value == 3
                else "Unknown" 
            )
            used_claim169_keys.add(14)

            # guardian = token_claim169.get(15)
            # used_claim169_keys.add(15)

            # Deprecated
            # binary_image = token_claim169.get(16)
            # used_claim169_keys.add(16)

            # Deprecated
            # _format_value = token_claim169.get(17)
            # binary_image_format = (
            #     "JPEG" if _format_value == 1
            #     else "JPEG2" if _format_value == 2
            #     else "AVIF" if _format_value == 3
            #     else "WEBP" if _format_value == 4
            #     else "Unknown"
            # )
            # used_claim169_keys.add(17)

            best_fingers = token_claim169.get(18)
            used_claim169_keys.add(18)

            # full_name_secondary = token_claim169.get(19)
            # used_claim169_keys.add(19)

            #TODO: perform ISO 639-3 languange code check
            # language_secondary = token_claim169.get(20)
            # used_claim169_keys.add(20)

            # location_code = token_claim169.get(21)
            # used_claim169_keys.add(21)

            # legal_status = token_claim169.get(22)
            # used_claim169_keys.add(22)

            issuing_country = token_claim169.get(23)
            used_claim169_keys.add(23)

            # 24 - 49 : For future - For Demographic Data attributes

            # right_thumb = token_claim169.get(50)
            # used_claim169_keys.add(50)

            # right_pointer_finger = token_claim169.get(51)
            # used_claim169_keys.add(51)

            # right_middle_finger = token_claim169.get(52)
            # used_claim169_keys.add(52)

            # right_ring_finger = token_claim169.get(53)
            # used_claim169_keys.add(53)

            # right_little_finger = token_claim169.get(54)
            # used_claim169_keys.add(54)

            # left_thumb = token_claim169.get(55)
            # used_claim169_keys.add(55)

            # left_pointer_finger = token_claim169.get(56)
            # used_claim169_keys.add(56)

            # left_middle_finger = token_claim169.get(57)
            # used_claim169_keys.add(57)

            # left_ring_finger = token_claim169.get(58)
            # used_claim169_keys.add(58)

            # left_little_finger = token_claim169.get(59)
            # used_claim169_keys.add(59)

            # right_iris = token_claim169.get(60)
            # used_claim169_keys.add(60)

            # left_iris = token_claim169.get(61)
            # used_claim169_keys.add(61)

            face_image = _to_base64_image(token_claim169.get(62))
            used_claim169_keys.add(62)

            # right_palm_print = token_claim169.get(63)
            # used_claim169_keys.add(63)

            # left_palm_print = token_claim169.get(64)
            # used_claim169_keys.add(64)

            # voice = token_claim169.get(65)
            # used_claim169_keys.add(65)

            # 66 - 74 : For future - For Biometrics Data attributes\

            # 75 - 99 : For future - For any other data

            uin = token_claim169.get(75)
            used_claim169_keys.add(75)
        
        else:
            raise ValueError(
                f"OpenLGU version {version} is not supported with curret QR code reader."
            )
    
    # Getting unused headers
    unused_payload_keys = set(payload.keys()) - used_payload_keys
    unused_claim169_keys = set(token_claim169.keys()) - used_claim169_keys
    
    if unused_payload_keys:
        print("Unused payload keys: ", unused_payload_keys)
    
    if unused_claim169_keys:
        print("Unused claim169 keys: ", unused_claim169_keys)

    id_details = QRDetails(
        token_issuer=token_issuer,
        token_issued_at=token_issued_at,
        pcn=pcn,
        version=version,
        language=language,
        full_name=full_name,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        gender=gender,
        address=address,
        email_id=email_id,
        phone_number=phone_number,
        nationality=nationality,
        marital_status=marital_status,
        best_fingers=best_fingers,
        issuing_country=issuing_country,
        face_image=face_image,
        uin=uin
    )

    return asdict(id_details)
