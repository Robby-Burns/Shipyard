def sanitize_db_url(url: str) -> str:
    """Sanitize database URL by obscuring the password in credentials.

    Correctly handles:
    - Multiple '@' characters in username or password
    - Missing schemes (e.g. 'user:pass@host/db')
    - SQLite URLs or URLs without credentials (no '@')
    """
    if not url:
        return ""

    if "@" not in url:
        return url

    if "://" in url:
        scheme, rest = url.split("://", 1)
        has_scheme = True
    else:
        scheme = ""
        rest = url
        has_scheme = False

    # The last '@' separates credentials from the host/port/database part
    creds, host_part = rest.rsplit("@", 1)

    if ":" in creds:
        # Split at the first ':' to isolate the username
        username, _ = creds.split(":", 1)
        sanitized_creds = f"{username}:***"
    else:
        sanitized_creds = "***"

    if has_scheme:
        return f"{scheme}://{sanitized_creds}@{host_part}"
    else:
        return f"{sanitized_creds}@{host_part}"
