from __future__ import annotations

GETVER = b"<GETVER>>"
GETSERIAL = b"<GETSERIAL>>"
GETCFG = b"<GETCFG>>"
GETCPM = b"<GETCPM>>"
BLOCK_SIZE = 4096
FC_ADDRESS = 0x1FC000
FD_ADDRESS = 0x1FD000
FE_ADDRESS = 0x1FE000
TARGET_ADDRESSES = (FC_ADDRESS, FD_ADDRESS, FE_ADDRESS)


def build_spir_command(address: int, length: int = BLOCK_SIZE) -> bytes:
    address = int(address)
    length = int(length)
    if not 0 <= address <= 0xFFFFFF:
        raise ValueError("SPIR address must fit in 24 bits")
    if not 1 <= length <= 0xFFFF:
        raise ValueError("SPIR length must fit in 16 bits")
    return b"<SPIR" + address.to_bytes(3, "big") + length.to_bytes(2, "big") + b">>"


def serial_number_text(payload: bytes) -> str | None:
    if not payload:
        return None
    return payload.hex(" ").upper()
