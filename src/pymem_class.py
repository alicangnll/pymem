import ctypes
import struct
import sys
import win32file
import os
from ctypes import *


def CTL_CODE(DeviceType, Function, Method, Access):
    return (DeviceType << 16) | (Access << 14) | (Function << 2) | Method
    
CTRL_IOCTRL = CTL_CODE(0x22, 0x101, 3, 3)
INFO_IOCTRL = CTL_CODE(0x22, 0x103, 3, 3)
INFO_IOCTRL_DEPRECATED = CTL_CODE(0x22, 0x100, 3, 3)

class PyMem:

    def GetInfoDeprecated(fd):
        result = win32file.DeviceIoControl(fd, INFO_IOCTRL_DEPRECATED, "", 1024, None)
        fmt_string = "QQl"
        offset = struct.calcsize(fmt_string)
        cr3, kpcr, number_of_runs = struct.unpack_from(fmt_string, result)
        for x in range(number_of_runs):
            start, length = struct.unpack_from("QQ", result, x * 16 + offset)
            print("0x%X\t\t0x%X" % (start, length))

    FIELDS = (["CR3", "NtBuildNumber", "KernBase", "KDBG"] +
              ["KPCR%02d" % i for i in range(32)] +
              ["PfnDataBase", "PsLoadedModuleList", "PsActiveProcessHead"] +
              ["Padding%s" % i for i in range(0xff)] +
              ["NumberOfRuns"])


    def MemoryParameters(fd):
        result = win32file.DeviceIoControl(fd, INFO_IOCTRL, b"", 102400, None)
        fmt_string = "Q" * len(PyMem.FIELDS)
        memory_parameters = dict(zip(PyMem.FIELDS, struct.unpack_from(fmt_string, result)))
        return memory_parameters

    def MemoryRuns(fd):
        runs = []
        result = win32file.DeviceIoControl(fd, INFO_IOCTRL, b"", 102400, None)
        fmt_string = "Q" * len(PyMem.FIELDS)
        memory_parameters = dict(zip(PyMem.FIELDS, struct.unpack_from(fmt_string, result)))
        offset = struct.calcsize(fmt_string)
        for x in range(memory_parameters["NumberOfRuns"]):
            start, length = struct.unpack_from("QQ", result, x * 16 + offset)
            runs.append((start, length))
        return runs

    def GetInfo(memory_parameters, runs):
        for k, v in sorted(memory_parameters.items()):
            if k.startswith("Pad"):
                continue

            if not v: continue

            print("%s: \t%#08x (%s)" % (k, v, v))

        print("Memory ranges:")
        print("Start\t\tEnd\t\tLength")

        for start, length in runs:
            print("0x%X\t\t0x%X\t\t0x%X" % (start, start+length, length))

    def SetMode(fd, modeset = "physical"):
        if modeset == "iospace":
            mode = 0
        elif modeset == "physical":
            mode = 1
        elif modeset == "pte":
            mode = 2
        elif modeset == "pte_pci":
            mode = 3
        else:
            raise RuntimeError("Mode %s not supported" % str(modeset))
        pack = struct.pack("I", mode)
        win32file.DeviceIoControl(fd, CTRL_IOCTRL, pack, 0, None)
        
    def PadWithNulls(buffer_size, outfd, length):
        while length > 0:
            to_write = min(length, buffer_size)
            outfd.write("\x00" * to_write)
            length -= to_write

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

    def dump_and_save_memory(filename):
        print("Creating AFF4 (Rekall) file")
        device_handle = win32file.CreateFile(
            "\\\\.\\pmem",
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL,
            None)
        # Set Modes and get informations
        PyMem.SetMode(device_handle)
        runs = PyMem.MemoryRuns(device_handle)
        memory_parameters = PyMem.MemoryParameters(device_handle)
        PyMem.GetInfo(memory_parameters, runs)
        # Write memory
        mem_addr = 0 # Starting Memory Address
        buf_size = 1024 * 1024
        while mem_addr < buf_size:
            win32file.SetFilePointer(device_handle, mem_addr, 0) # Setting pointer
            data = win32file.ReadFile(device_handle, buf_size)[1] # Reading memory...
            with open(filename + ".aff", "wb") as outfd:
                outfd.write(data) # Writing to file
            outfd.close()
            mem_addr += buf_size
            print(f"Dumped {mem_addr} / {buf_size} bytes ({mem_addr * 100 / buf_size:.2f}%)")
        sys.stdout.flush()
        win32file.CloseHandle(device_handle)