# MOSIP Library
A Python library that parses MOSIP API responses from the [MOSIP Auth SDK](https://docs.mosip.io/1.2.0/id-lifecycle-management/identity-verification/id-authentication-services/mosip-authentication-sdk) into validated Python objects using [Pydantic](https://docs.pydantic.dev/latest/).

## Setting Up
1) Configure the `mosip_config.toml` located at `./mosip/mosip_config.toml` with your MOSIP API credentials.
2) Run MOSIP tests.
```py
python manage.py test mosip
```

## Classes
### MOSIPResponse
HTTP Response from MOSIP API transactions.
#### Fields
| Attribute        | Type                                       | Description        |
|------------------|--------------------------------------------|--------------------|
| `transaction_id` | `str`                                      | Transaction ID     |
| `version`        | `str`                                      | Version            |
| `id`             | `str`                                      | ID                 |
| `errors`         | `list[MOSIPResponseError]`                 | Errors encountered |
| `response_time`  | `str`                                      | Time of response   |
| `response`       | `MOSIPUser` \| `MOSIPAuthStatus` \| `None` | Result of response |