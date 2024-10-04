# Portal C code

This is a collection of C modules with algorithm that can run faster than the native Python implementation. 
The C code is compiled into a shared library that can be imported into Python using the `ctypes` module.



## Compilation
Make sure you have a `gcc` compiler installed on your system. You can download the MSYS2 compiler from [here](https://www.msys2.org/#installation).

> Usually you don't need to compile the C code yourself, as the shared library is already provided in the `portal/bin` folder.
> But just in case you want to compile it yourself or make changes to the C code, follow the instructions below.
### Automatic compilation
Execute `compile.bat` to compile the C code into a shared library. It will automatically generate the `.dll` file and place in the `portal/bin` folder.

### Manual compilation
To compile the module, run the following command:

```bash
gcc -shared -o crc16-ccitt.dll crc16-ccitt.c
```