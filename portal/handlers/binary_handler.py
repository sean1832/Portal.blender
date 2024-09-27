import gzip
import io
import struct

from ..data_struct.packet import PacketHeader


class BinaryHandler:
    @staticmethod
    def parse_header(data: bytes) -> PacketHeader:
        # see https://docs.python.org/3/library/struct.html#format-characters
        is_compressed, is_encrypted, checksum, size = struct.unpack(
            "??Hi", data[: PacketHeader.get_expected_size()]
        )
        return PacketHeader(is_encrypted, is_compressed, size, checksum)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        if not data[:2] == b"\x1f\x8b":
            raise ValueError("Data is not in gzip format.")
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
            try:
                return gz.read()
            except OSError:
                return data
    
    @staticmethod
    def compress(data: bytes) -> bytes:
        with io.BytesIO() as compressed_data:
            with gzip.GzipFile(fileobj=compressed_data, mode="wb") as gz:
                gz.write(data)
            return compressed_data.getvalue()
