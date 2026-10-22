"""Utilities shared with the ESP32 access-code algorithm."""


def normalize_code(value: str) -> str:
    """Keep alphanumeric characters and convert them to uppercase."""
    return "".join(character for character in value if character.isalnum()).upper()


def derive_access_code(rfid_uid: str) -> str:
    """Return the eight-character FNV-1a code expected by the ESP32."""
    normalized_uid = normalize_code(rfid_uid)
    hash_value = 2166136261
    for character in normalized_uid.encode("ascii"):
        hash_value ^= character
        hash_value = (hash_value * 16777619) & 0xFFFFFFFF
    return f"{hash_value:08X}"
