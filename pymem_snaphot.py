import psutil
from ctypes import WinDLL, create_string_buffer, addressof, windll, c_uint

class PyMemSnapshot:
    def get_memimg_win(name):
        try:
            print("--------------- PyMem Capture v1 ---------------")
            k32 = WinDLL('kernel32')
            size = int(psutil.virtual_memory().total)
            buffer = create_string_buffer(size)
            address = addressof(buffer)
            k32.ReadProcessMemory(windll.kernel32.GetCurrentProcess(), c_uint(address), buffer, c_uint(size), None)
            print(f"Writing {size} memory image {address} to {name}...")
            with open(str(name), "wb") as f:
                f.write(buffer.raw)
        except Exception as e:
            print("FATAL ERROR : IMAGE CAN NOT GET\nREASON : " + str(e))

