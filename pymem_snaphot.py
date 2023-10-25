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

    def create_raw_file(filename, memsize):
        print("Creating RAW file")
        k32 = WinDLL("kernel32")
        buffer = create_string_buffer(memsize)
        address = addressof(buffer)
        k32.ReadProcessMemory(
            windll.kernel32.GetCurrentProcess(),
            c_uint(address),
            buffer,
            c_uint(memsize),
            None,
        )
        print(f"Creating {memsize} memory RAW image {address} to {filename}...")
        with open(str(filename), "wb") as f:
            f.write(buffer.raw)
        f.close()

    def dump_and_save_memory(filename):
        print("--------------- PyMem Capture v1 ---------------")
        k32 = WinDLL("kernel32")  # Import kernel32
        stat = MEMORYSTATUSEX()
        k32.GlobalMemoryStatusEx(byref(stat))
        memsize = int(stat.ullTotalPhys)  # Get all memory bytes
        PyMem.create_raw_file(filename, memsize)
        device_handle = win32file.CreateFile(
            "\\\\.\\pmem",
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL,
            None,
        )
        mem_addr = 0
        buf_size = 1024 * 1024
        while mem_addr < memsize:
            win32file.SetFilePointer(device_handle, mem_addr, 0)
            data = win32file.ReadFile(device_handle, buf_size)[1]
            with open(filename, "wb") as f:
                f.write(data)
            f.close()
            print(
                f"Dumped {mem_addr} / {memsize} bytes ({mem_addr * 100 / memsize:.2f}%)"
            )
            mem_addr += buf_size
        win32file.CloseHandle(device_handle)

if __name__ == "__main__":
    PyMem.service_create()
    PyMem.dump_and_save_memory("demo.raw")