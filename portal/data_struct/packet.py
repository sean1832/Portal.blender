import struct


class PacketHeader:
    def __init__(self, is_encrypted, is_compressed, size, checksum):
        self.is_compressed = is_compressed
        self.is_encrypted = is_encrypted
        self.size = size
        self.checksum = checksum

    @property
    def IsCompressed(self):
        return self.is_compressed

    @property
    def IsEncrypted(self):
        return self.is_encrypted

    @property
    def Size(self):
        return self.size

    @property
    def Checksum(self):
        return self.checksum

    @staticmethod
    def get_expected_size():
        # see
        return 8  # 1 + 1 + 2 + 4


class Packet:
    MAGIC_NUMBER = b"pk"  # pk

    def __init__(
        self,
        data: bytes,
        size: int | None = None,
        checksum: int | None = None,
        is_encrypted: bool | None = None,
        is_compressed: bool | None = None,
        header: PacketHeader | None = None,
    ):
        self.data = data
        if header is not None:
            self.header = header
        else:
            computed_size = size if size is not None else len(data)
            self.header = PacketHeader(is_encrypted, is_compressed, computed_size, checksum)

    def serialize(self) -> bytes:
        header_bytes = bytearray()
        header_bytes.extend(Packet.MAGIC_NUMBER)  # magic number
        header_bytes.append(1 if self.header.is_compressed else 0)  # is_compressed flag
        header_bytes.append(1 if self.header.is_encrypted else 0)  # is_encrypted flag
        header_bytes.extend(struct.pack("H", self.header.checksum))  # checksum
        header_bytes.extend(struct.pack("i", self.header.size))  # size
        return bytes(header_bytes) + self.data  # combine header and data

    @staticmethod
    def validate_magic_number(data):
        # minimum size of a packet is the magic number and the header
        if len(data) < len(Packet.MAGIC_NUMBER):
            raise ValueError("Data is too short to be a valid packet")

        # check magic number
        if data[: len(Packet.MAGIC_NUMBER)] != Packet.MAGIC_NUMBER:
            raise ValueError("Data does not contain the magic number")

    @staticmethod
    def deserialize(data):
        Packet.validate_magic_number(data)
        index = len(Packet.MAGIC_NUMBER)  # start after magic number
        header = Packet.deserialize_header(data, index)

        payload_data = data[
            index + PacketHeader.get_expected_size() : index
            + PacketHeader.get_expected_size()
            + header.Size
        ]
        packet = Packet(payload_data, header=header)

        return packet

    @staticmethod
    def deserialize_header(data, index):
        # read flags
        is_compressed = data[index] == 1
        index += 1
        is_encrypted = data[index] == 1
        index += 1

        # read checksum
        checksum = struct.unpack_from("H", data, index)[0]
        index += struct.calcsize("H")

        # read size
        size = struct.unpack_from("i", data, index)[0]
        index += struct.calcsize("i")

        return PacketHeader(is_encrypted, is_compressed, size, checksum)

    @staticmethod
    def deserialize_header_start(data, start_index=0):
        return Packet.deserialize_header(data, start_index)
