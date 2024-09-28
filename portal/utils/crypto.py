class Crc16:
    POLYNOMIAL = 0xA001  # A001 is the Crc16 polynomial

    def __init__(self):
        self._table = [0] * 256
        for i in range(256):
            value = 0
            temp = i
            for _ in range(8):
                if (value ^ temp) & 0x0001:
                    value = (value >> 1) ^ self.POLYNOMIAL
                else:
                    value >>= 1
                temp >>= 1
            self._table[i] = value

    def compute_checksum(self, byte_array: bytes) -> int:
        """Generate a CRC16 checksum for the given byte array."""
        crc = 0
        for byte in byte_array:
            index = (crc ^ byte) & 0xFF
            crc = (crc >> 8) ^ self._table[index]
        return crc
