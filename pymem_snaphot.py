import psutil

class PyMemSnapshot:
    def get_memimg_win(name):
        # Import the ctypes and psutil module
        import ctypes, psutil
        # Import kernel32
        k32 = ctypes.WinDLL('kernel32')
        # Get total RAM size bytes
        size = int(psutil.virtual_memory().total)
        # Allocate a buffer of the given size
        buffer = ctypes.create_string_buffer(size)
        # Get the address of the buffer
        address = ctypes.addressof(buffer)
        # Read the memory from the current process at the given address
        k32.ReadProcessMemory(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.c_uint(address), buffer, ctypes.c_uint(size), None)
        with open(str(name), "wb") as f:
            f.write(buffer.raw)

    def get_procimg_win(memory_name, pid):
        import ctypes
        import win32process
        from ctypes import wintypes
        # Define the constants and types
        MAX_PATH = 260
        PROCESS_ALL_ACCESS = 0x1F0FFF
        HMODULE = wintypes.HMODULE
        # VOID Values
        LPVOID = ctypes.c_void_p
        LPCVOID = ctypes.c_void_p
        HANDLE = wintypes.HANDLE
        DWORD = wintypes.DWORD
        LPWSTR = wintypes.LPWSTR
        # Get the kernel32 and psapi libraries
        k32 = ctypes.WinDLL('kernel32')
        psapi = ctypes.WinDLL('psapi')
        # Set the argument types and return types of the functions
        # OpenProcess args
        k32.OpenProcess.argtypes = DWORD, wintypes.BOOL, DWORD
        k32.OpenProcess.restype = HANDLE
        # ReadProcessMemory args
        k32.ReadProcessMemory.argtypes = HANDLE, LPCVOID, LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
        k32.ReadProcessMemory.restype = wintypes.BOOL
        # GetMappedFileNameW args
        psapi.GetMappedFileNameW.argtypes = HANDLE, LPVOID, LPWSTR, DWORD
        psapi.GetMappedFileNameW.restype = DWORD
        # EnumProcessModules args
        psapi.EnumProcessModules.argtypes = [HANDLE, ctypes.POINTER(HMODULE), DWORD, ctypes.POINTER(DWORD)]
        psapi.EnumProcessModules.restype = wintypes.BOOL
        # CloseHandle args
        k32.CloseHandle.argtypes = HANDLE,
        k32.CloseHandle.restype = wintypes.BOOL
        # Open the process with query and read access
        process = k32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        # Define the process ID and address to read from
        modules = win32process.EnumProcessModules(process)
        addr = modules[0] # Select the first item in the list
        # Read pid bytes from the address
        buffer = ctypes.create_string_buffer(255)
        bytes_read = ctypes.c_size_t()
        result = k32.ReadProcessMemory(process, addr, buffer, len(buffer), ctypes.byref(bytes_read))
        # Check if the read was successful
        if modules:
            print(f"PID: {pid}")
            print(f"Base address: {addr}")
            if result:
                # Get the file name mapped to the address
                file_name = ctypes.create_unicode_buffer(MAX_PATH)
                length = psapi.GetMappedFileNameW(process, addr, file_name, MAX_PATH)
                # Check if the file name was retrieved
                if length:
                    # Print the file name and the data read
                    print(f"Kernel layer name: {file_name.value}")
                    with open(str(memory_name), "wb") as f:
                        f.write(buffer.raw)
                    return True
                else:
                    # Print an error message
                    return f"Could not get the kernel layer name. Error code: {ctypes.get_last_error()}"
            else:
                # Print an error message
                return f"Could not read from the address. Error code: {ctypes.get_last_error()}"

        else:
            # Print an error message
            print(f"Could not read from the address. Error code: {ctypes.get_last_error()}")
            
        k32.CloseHandle(process)


