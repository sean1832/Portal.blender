import ctypes
import os
from ctypes import POINTER, c_size_t, c_ubyte, c_uint16


class Crc16:
    def __init__(self) -> None:
        # get the full path of the DLL
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dll_path = os.path.abspath(os.path.join(root, "bin/crc16-ccitt.dll"))

        # load the DLL
        self.dll = ctypes.CDLL(dll_path)

        # initialize function prototype
        self.dll.crc_init.restype = c_uint16
        self.dll.crc_update.argtypes = [
            c_uint16,           # crc_t crc
            POINTER(c_ubyte),   # const void *data
            c_size_t            # size_t data_len
            ] 
        self.dll.crc_update.restype = c_uint16
        self.dll.crc_finalize.argtypes = [c_uint16]
        self.dll.crc_finalize.restype = c_uint16

    def compute_checksum(self, byte_array: bytes) -> int:
        # initialize the crc
        crc = self.dll.crc_init()

        # convert the byte array to a c_ubyte array
        data_len = len(byte_array)
        data_array = (c_ubyte * data_len)(*byte_array)

        # update the crc
        crc = self.dll.crc_update(crc, data_array, data_len)

        # finalize the crc
        crc = self.dll.crc_finalize(crc)

        return crc
