@ECHO OFF
gcc -shared -o ../portal/bin/crc16-ccitt.dll crc16/crc16-ccitt.c

echo Compilation done. Find the DLL in the `portal/bin` folder.
pause