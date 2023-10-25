import psutil
import pywintypes, os, ctypes
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
    def ready():
        program_pid = os.getpid()
        processes = psutil.process_iter()
        for process in processes:
            process_name = process.name()
            process_pid = process.pid
            if process_name in ["System", "cmd.exe"]:
                continue
            if process_pid == program_pid:
                continue
        try:
            process.kill()
            print(f"{process_name} ({process_pid}) kapatıldı.")
        except:
            print(f"{process_name} ({process_pid}) kapatılamadı.")

    def service_create():
        try:
            PyMem.ready()
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
        device_handle = pywintypes.CreateFile(
            "\\\\.\\pmem",
            pywintypes.GENERIC_READ | pywintypes.GENERIC_WRITE,
            pywintypes.FILE_SHARE_READ | pywintypes.FILE_SHARE_WRITE,
            None,
            pywintypes.OPEN_EXISTING,
            pywintypes.FILE_ATTRIBUTE_NORMAL,
            None,
        )
        mem_addr = 0
        buf_size = 1024 * 1024
        while mem_addr < memsize:
            pywintypes.SetFilePointer(device_handle, mem_addr, 0)
            data = pywintypes.ReadFile(device_handle, buf_size)[1]
            with open(filename, "wb") as f:
                f.write(data)
            f.close()
            print(
                f"Dumped {mem_addr} / {memsize} bytes ({mem_addr * 100 / memsize:.2f}%)"
            )
            mem_addr += buf_size
        pywintypes.CloseHandle(device_handle)


if __name__ == "__main__":
    PyMem.service_create()
    PyMem.dump_and_save_memory("demo.raw")