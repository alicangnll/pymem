import psutil

class PyMemSnapshot:
    def get_memimg_win(name):
        import ctypes, psutil
        k32 = ctypes.WinDLL('kernel32')
        size = int(psutil.virtual_memory().total)
        buffer = ctypes.create_string_buffer(size)
        address = ctypes.addressof(buffer)
        k32.ReadProcessMemory(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.c_uint(address), buffer, ctypes.c_uint(size), None)
        with open(str(name), "wb") as f:
            f.write(buffer.raw)

