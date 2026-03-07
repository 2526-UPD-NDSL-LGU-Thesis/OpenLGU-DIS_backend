from main import sign_eddsa, verify_eddsa
import json

def main():
    payload = {
        "Name" : "James"
    }

    msg = sign_eddsa(payload)

    verify_eddsa(msg)


if __name__ == "__main__" :
    main()