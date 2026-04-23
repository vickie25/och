import json
import os
import urllib.request


def main() -> int:
    token = os.environ.get("TOKEN")
    if not token:
        print("MISSING_TOKEN")
        return 2

    url = os.environ.get("URL", "http://127.0.0.1:8001/api/v1/profiling/session/start")
    req = urllib.request.Request(
        url,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    body = json.dumps({}).encode("utf-8")

    try:
        with urllib.request.urlopen(req, data=body, timeout=15) as resp:
            raw = resp.read().decode("utf-8", "replace")
            print("STATUS", resp.status)
            print("BODY", raw[:800])
            return 0
    except Exception as e:
        # urllib wraps non-2xx as HTTPError, includes status+body
        if hasattr(e, "code"):
            print("STATUS", getattr(e, "code"))
            try:
                raw = e.read().decode("utf-8", "replace")  # type: ignore[attr-defined]
                print("BODY", raw[:800])
            except Exception:
                print("BODY_READ_FAILED")
            return 1

        print("ERROR", type(e).__name__, str(e)[:800])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

