import os


KEYS = [
    "MAIL_HOST",
    "MAIL_PORT",
    "MAIL_USERNAME",
    "MAIL_PASSWORD",
    "MAIL_FROM_ADDRESS",
    "MAIL_FROM_NAME",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
]


def main() -> int:
    print("MAIL_ENV_STATUS")
    for k in KEYS:
        v = os.environ.get(k)
        print(f"{k}={'<set>' if v else '<missing>'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

