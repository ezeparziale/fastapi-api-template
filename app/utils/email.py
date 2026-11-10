def normalize_email(email: str) -> str:
    """
    ### Normalize an email address.

    Trims surrounding whitespace and lowercases the whole address so emails
    are stored and compared case-insensitively.

    Args:
        email: The email address to normalize.

    Returns:
        str: The normalized email address.
    """
    return email.strip().lower()
