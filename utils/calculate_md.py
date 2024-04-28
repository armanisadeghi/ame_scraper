import hashlib


def calculate_md5_hash(content):
    """Calculate the MD5 hash of the given content."""
    # Ensure the content is bytes, encode if it's not
    if isinstance(content, str):
        content = content.encode('utf-8')

    # Create md5 hash object
    md5 = hashlib.md5()

    # Update the hash object with the bytes
    md5.update(content)

    # Return the hexadecimal MD5 hash
    return md5.hexdigest()
