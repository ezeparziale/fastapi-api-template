import bcrypt


def get_password_hash(password: str) -> str:
    """
    ### Generate a password hash using bcrypt.

    Args:
        password: The password to hash.

    Returns:
        str: The hashed password.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    ### Verify if a plain password matches its hash.

    Args:
        plain_password: The plain password.
        hashed_password: The hashed password.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    hashed_password_bytes = hashed_password.encode("utf-8")
    plain_password_bytes = plain_password.encode("utf-8")
    return bcrypt.checkpw(
        password=plain_password_bytes, hashed_password=hashed_password_bytes
    )
