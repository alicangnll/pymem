import time
import win32file, os, ctypes
from ctypes import *

class MEMORYSTATUSEX(Structure):
    _fields_ = [
        ("dwLength", c_ulong),
        ("dwMemoryLoad", c_ulong),
        ("ullTotalPhys", c_ulonglong),
        ("ullAvailPhys", c_ulonglong),
        ("ullTotalPageFile", c_ulonglong),
        ("ullAvailPageFile", c_ulonglong),
        ("ullTotalVirtual", c_ulonglong),
        ("ullAvailVirtual", c_ulonglong),
        ("sullAvailExtendedVirtual", c_ulonglong),
    ]

    def __init__(self):
        # MEMORYSTATUSEX boyutuna eşit olacak şekilde bunu başlatmak zorundayız
        self.dwLength = sizeof(self)
        super(MEMORYSTATUSEX, self).__init__()

def service_create():
    try:
        os.system(f"net stop winpmem") # Stop any previous instance of the driver
        os.system(f"sc delete winpmem") # Delete any previous instance of the driver
        if ctypes.sizeof(ctypes.c_voidp) == 4:
            driver_path = "winpmem_x86.sys"
        else:
            driver_path = "winpmem_x64.sys"
        # Create a new instance of the driver
        cwd = os.getcwd()
        os.system('sc create winpmem type=kernel binPath="' + cwd + '//' + driver_path + '"')
        print("WinPMEM Service Created")
        # Start the new instance of the driver
        os.system(f"net start winpmem")
        print("WinPMEM Driver Created")
    except Exception as e:
        print("ERROR : WinPMEM can not created. Reason : " + str(e))

def dump_and_save_memory(device_handle, memsize, filename):
    print("Dumping started")
    mem_addr = 0
    buf_size = 1024 * 1024
    while mem_addr < memsize:
        win32file.SetFilePointer(device_handle, mem_addr, 0)
        data = win32file.ReadFile(device_handle, buf_size)[1]
        print(f"Writing {mem_addr} to {filename}")
        with open(filename, "wb") as f:
            f.write(data)
        data = ""
        mem_addr += buf_size
        time.sleep(15)
    win32file.CloseHandle(device_handle)

service_create()
fd = win32file.CreateFile("\\\\.\\pmem", win32file.GENERIC_READ | win32file.GENERIC_WRITE, win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE, None, win32file.OPEN_EXISTING, win32file.FILE_ATTRIBUTE_NORMAL, None)
k32 = WinDLL('kernel32')
stat = MEMORYSTATUSEX()
k32.GlobalMemoryStatusEx(byref(stat))
mem_size = int(stat.ullTotalPhys) # Get all memory bytes
filename ="demo.raw"
dump_and_save_memory(fd, mem_size, filename)