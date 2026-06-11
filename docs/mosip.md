# MOSIP Library
A Python library that parses MOSIP API responses from the [MOSIP Auth SDK](https://docs.mosip.io/1.2.0/id-lifecycle-management/identity-verification/id-authentication-services/mosip-authentication-sdk) into validated Python objects using [Pydantic](https://docs.pydantic.dev/latest/).

## Setting Up
1) Acquire the access credentials to a MOSIP server. Usually these includes:
- `keystore-signed.p12`
- `keystore.p12`
- `partner.pem`
2) Configure the `mosip_config.toml` located at `./mosip/mosip_config.toml` with your MOSIP API credentials. Update the Django `CONFIG_MOSIP_SETTINGS` from the `app/settings.py` with the path to the config being used. 
3) Run MOSIP tests.
```py
python manage.py test mosip
```
4) If all tests came out successful, then set up is complete. Otherwise, consult the test results.



## Authenticator
MOSIP authenticator manager that helps set up MOSIP Authenticator for use.

### MOSIPAuthManager
Manager for MOSIP Authenticator. Sets up authenticator upon runtime. Raises a `RuntimeError` if authenticator failed to initialize.


## Decorators
MOSIP decorators for integration with other apps in the project.

### `require_mosip(urls, timeout, require_all=False)`
A function decorator that checks the connection with MOSIP API servers. Returns a REST `Response` if an error occurs.

### `require_mosip(urls, timeout, require_all=False)`
A function decorator that checks the connection with MOSIP API servers. Returns a `ValueError` if an error occurs.



## Models
MOSIP Pydantic models for MOSIP SDK. 

The MOSIP Python Auth SDK alone is enough to access the MOSIP server. What this library does is convert MOSIP responses to Python objects using Pydantic models for a much cleaner integration while working with the MOSIP SDK.

### Overview

![MOSIP Library UML Diagram](<images/MOSIP - models.png>)

A class heirarchy approach was taken given the various MOSIP response models, and in consideration of future extensions of MOSIP trasaction types and authentication methods. This heirarchy is represented in the diagram above.

### MOSIPUser
KYC result of a user in MOSIP.

#### Attributes
| Name         | Type                                    | Description                   |
|--------------|-----------------------------------------|-------------------------------|
| `name`       | List[[language_dict](#language_dict)] | Full name                     |
| `gender`     | List[[language_dict](#language_dict)] | Gender                        |
| `dob`        | str                                   | Date of birth                 |
| `location1`  | List[[language_dict](#language_dict)] | Address city                  |
| `location3`  | List[[language_dict](#language_dict)] | Address province              |
| `zone`       | List[[language_dict](#language_dict)] | Address barangay              |
| `postalCode` | str                                   | Address postal code           |
| `phone`      | str                                   | Phone number                  |
| `email`      | str                                   | Email address                 |
| `face`       | str                                   | Face image (in Base64 string) |

##### language_dict
Dictionary representation of an attribute in different languages, following [ISO 639-3 language code format](https://iso639-3.sil.org/code_tables/639/data) for dictionary keys.
```JSON
{
    "language" : "<lang-code>",
    "value"    : "<value>"
}
```

#### Methods
##### `from_demographics()`
Creates a `MOSIPUser` from MOSIP SDK response.

##### `flatten()`
Returns a single-level dictionary of the User's attributes. Uses english as default for multi-language attributes.



### MOSIPResponseError
MOSIP errors from a MOSIP SDK response.

#### Attributes
| Name             | Type             | Description                   |
|------------------|------------------|-------------------------------|
| `error_code`     | str              | MOSIP error code              |
| `error_message`  | str              | Error description             |
| `action_message` | Optional[str]    | Possible actions to fix error |



### MOSIPBaseResponseStatus
Reponse status of a MOSIP transaction.

#### Attributes
| Name          | Type  | Description                                         |
|---------------|-------|-----------------------------------------------------|
| `status`      | bool  | Auth Status of MOSIP transaction, success or failed |
| `session_key` | str   | MOSIP transaction session key                       |
| `identity`    | str   | Transaction requestor identity                      |
| `thumbprint`  | str   | Transaction requestor certificate fingerprint       |
| `auth_token`  | str   | Transaction authentication token                    |



### MOSIPBaseResponse
Base response model for MOSIP API transactions.

#### Attributes
| Name             | Type                                                | Description        |
|------------------|-----------------------------------------------------|--------------------|
| `transaction_id` | str                                                 | Transaction ID     |
| `version`        | str                                                 | Version            |
| `id`             | str                                                 | ID                 |
| `errors`         | List[[MOSIPResponseError](#mosipresponseerror)]     | Errors encountered |
| `response_time`  | str                                                 | Response time      |
| `response`       | [MOSIPBaseResponseStatus](#mosipbaseresponsestatus) | Transaction result |

#### Methods

##### `from_demographics()`
Creates a `MOSIPBaseResponse` from MOSIP SDK response.

##### `status`
Returns HTTP status of MOSIP transaction.

##### `error_messages`
Returns a list of MOSIP errors. Returns an empty list if no errors encountered.



### MOSIPKYCResponse
KYC response model for MOSIP API transactions. Inherits from the [MOSIPBaseResponse](#mosipbaseresponse) class.

#### Attributes
| Name             | Type                                                | Description        |
|------------------|-----------------------------------------------------|--------------------|
| `transaction_id` | str                                                 | Transaction ID     |
| `version`        | str                                                 | Version            |
| `id`             | str                                                 | ID                 |
| `errors`         | List[[MOSIPResponseError](#mosipresponseerror)]     | Errors encountered |
| `response_time`  | str                                                 | Response time      |
| `response`       | [MOSIPBaseResponseStatus](#mosipbaseresponsestatus) | Transaction result |
| `user`           | [MOSIPUser](#mosipuser)                             | User from result   |

#### Methods

##### `from_demographics()`
Creates a `MOSIPKYCResponse` from MOSIP SDK response.

##### `status`
Returns HTTP status of MOSIP transaction.

##### `error_messages`
Returns a list of MOSIP errors. Returns an empty list if no errors encountered.

#### Sample Usage
```python
from mosip.models import MOSIPKYCResponse

mosip_response = MOSIPKYCResponse.from_demographics(
    uid=uid, name=name, dob=dob, gender=gender
)

if mosip_response.status:
    print(mosip_response.model_dumps())
```



### MOSIPAuthResponse
Auth response model for MOSIP API transactions. Inherits from the [MOSIPBaseResponse](#mosipbaseresponse) class.

#### Attributes
| Name             | Type                                                | Description        |
|------------------|-----------------------------------------------------|--------------------|
| `transaction_id` | str                                                 | Transaction ID     |
| `version`        | str                                                 | Version            |
| `id`             | str                                                 | ID                 |
| `errors`         | List[[MOSIPResponseError](#mosipresponseerror)]     | Errors encountered |
| `response_time`  | str                                                 | Response time      |
| `response`       | [MOSIPBaseResponseStatus](#mosipbaseresponsestatus) | Transaction result |

#### Methods

##### `from_demographics()`
Creates a `MOSIPAuthResponse` from MOSIP SDK response.

##### `status`
Returns HTTP status of MOSIP transaction.

##### `error_messages`
Returns a list of MOSIP errors. Returns an empty list if no errors encountered.

#### Sample Usage
```python
from mosip.models import MOSIPAuthResponse

mosip_response = MOSIPAuthResponse.from_demographics(
    uid=uid, name=name, dob=dob, gender=gender
)

if mosip_response.status:
    print(mosip_response.model_dumps())
```