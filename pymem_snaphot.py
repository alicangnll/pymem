class PyMemSnapshot:
    def get_memimg_win(name):
        # Import the ctypes and psutil module
        import ctypes, psutil
        # Memory dump name
        # Get total RAM size bytes
        size = int(psutil.virtual_memory().total)
        # Allocate a buffer of the given size
        buffer = ctypes.create_string_buffer(size)
        # Get the address of the buffer
        address = ctypes.addressof(buffer)
        # Read the memory from the current process at the given address
        ctypes.windll.kernel32.ReadProcessMemory(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.c_uint(address), buffer, ctypes.c_uint(size), None)
        with open(str(name), "wb") as f:
            f.write(buffer.raw)
