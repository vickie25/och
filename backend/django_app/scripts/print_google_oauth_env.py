import os


KEYS = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_OAUTH_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "FRONTEND_URL",
]


def main() -> int:
    print("GOOGLE_OAUTH_ENV_STATUS")
    for k in KEYS:
        v = os.environ.get(k)
        if k.endswith("SECRET"):
            print(f"{k}={'<set>' if v else '<missing>'}")
        else:
            # IDs / frontend url are not passwords, but still don't dump values here.
            print(f"{k}={'<set>' if v else '<missing>'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

