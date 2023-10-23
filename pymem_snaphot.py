import os, sys
from ctypes import WinDLL, create_string_buffer, addressof, windll, c_uint, c_ulong, c_ulonglong, Structure, sizeof, byref

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


class PyMemSnapshot:
    def get_memimg_win(name):
        try:
            if os.name == "nt":
                # Check system Windows or not
                if name == "" or name is None:
                    # Check space chars
                    print("FATAL ERROR : IMAGE CAN NOT GET!")
                else: 
                    print("--------------- PyMem Capture v1 ---------------")
                    k32 = WinDLL('kernel32') # Import kernel32
                    stat = MEMORYSTATUSEX()
                    k32.GlobalMemoryStatusEx(byref(stat))
                    size = int(stat.ullTotalPhys) # Get all memory bytes
                    buffer = create_string_buffer(size) # Creating allocated size
                    address = addressof(buffer) # Addressing all memory
                    k32.ReadProcessMemory(windll.kernel32.GetCurrentProcess(), c_uint(address), buffer, c_uint(size), None) # Reading all memory
                    print(f"Writing {size} memory image {address} to {name}...")
                    with open(str(name), "wb") as f:
                        f.write(buffer.raw) # Writing all memory informations to RAW file
            else:
                print("FATAL ERROR : OS ARE NOT SUPPORTING!")
                sys.exit(0)
        except Exception as e:
            print("FATAL ERROR : IMAGE CAN NOT GET\nREASON : " + str(e))

