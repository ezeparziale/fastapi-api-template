import logging

from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.INFO)


logging.info("Generating encryption key...")
encryption_key = Fernet.generate_key().decode()
logging.info(f"ENCRYPTION_KEY={encryption_key}")
logging.info("Encryption key generated.")
