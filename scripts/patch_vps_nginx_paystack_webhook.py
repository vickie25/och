from __future__ import annotations

from pathlib import Path


TARGET = Path("/var/www/och/nginx/conf.d/local.conf")


LOCATION_BLOCK = """
    # Paystack webhook (Paystack calls a root URL, but Django lives under /api/)
    location ^~ /paystack/webhook/ {
        rewrite ^/paystack/webhook/?$ /api/v1/paystack/webhook/ break;
        proxy_pass http://hub_prod_django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $forwarded_proto;
    }
""".strip(
    "\n"
)


def main() -> int:
    if not TARGET.exists():
        print("MISSING", str(TARGET))
        return 2

    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    if "location ^~ /paystack/webhook/" in text:
        print("ALREADY_OK")
        return 0

    needle = "    # Backend API (Django)\n"
    idx = text.find(needle)
    if idx == -1:
        print("NEEDLE_NOT_FOUND")
        return 3

    patched = text[:idx] + LOCATION_BLOCK + "\n\n" + text[idx:]
    TARGET.write_text(patched, encoding="utf-8")
    print("PATCHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

