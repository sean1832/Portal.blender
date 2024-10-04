#ifndef CRC16_CCITT_H
#define CRC16_CCITT_H

#include <stdlib.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifdef _WIN32
  #define DLL_EXPORT __declspec(dllexport)
#else
  #define DLL_EXPORT
#endif

#define CRC_ALGO_TABLE_DRIVEN 1
typedef uint_fast16_t crc_t;

DLL_EXPORT crc_t crc_init(void);
DLL_EXPORT crc_t crc_update(crc_t crc, const void *data, size_t data_len);
DLL_EXPORT crc_t crc_finalize(crc_t crc);

#ifdef __cplusplus
}           /* closing brace for extern "C" */
#endif

#endif      /* CRC16_CCITT_H */
