import win32file, os, ctypes
from ctypes import *

class PyMem:
    def service_create():
        try:
            os.system(f"net stop winpmem")  # Stop any previous instance of the driver
            os.system(
                f"sc delete winpmem"
            )  # Delete any previous instance of the driver
            if ctypes.sizeof(ctypes.c_voidp) == 4:
                if os.path.isfile("winpmem_x86.sys") is True:
                    driver_path = "winpmem_x86.sys"
                else:
                    return "Driver file are not found"
            else:
                if os.path.isfile("winpmem_x64.sys") is True:
                    driver_path = "winpmem_x64.sys"
                else:
                    return "Driver file are not found"
            # Create a new instance of the driver
            cwd = os.getcwd()
            os.system(
                'sc create winpmem type=kernel binPath="'
                + cwd
                + "//"
                + driver_path
                + '"'
            )
            print("WinPMEM Service Created")
            # Start the new instance of the driver
            os.system(f"net start winpmem")
            print("WinPMEM Driver Created")
        except Exception as e:
            print("ERROR : WinPMEM can not created. Reason : " + str(e))

    def dump_and_save_memory(filename, memsize = 1024 * 1024):
        print("Creating AFF4 (Rekall) file")
        device_handle = win32file.CreateFile(
            "\\\\.\\pmem",
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL,
            None,
        )
        mem_addr = 0 # Starting Memory Address
        while mem_addr < memsize:
            win32file.SetFilePointer(device_handle, mem_addr, 0) # Setting pointer
            data = win32file.ReadFile(device_handle, memsize)[1] # Reading memory...
            with open(filename + ".aff", "wb") as f:
                f.write(data) # Writing to file
            f.close()
            mem_addr += memsize
            print(f"Dumped {mem_addr} / {memsize} bytes ({mem_addr * 100 / memsize:.2f}%)")
        win32file.CloseHandle(device_handle)
