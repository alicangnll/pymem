import ctypes
import struct
import sys
import win32file
import win32service
import os
from ctypes import *


def CTL_CODE(DeviceType, Function, Method, Access):
    return (DeviceType << 16) | (Access << 14) | (Function << 2) | Method
    
CTRL_IOCTRL = CTL_CODE(0x22, 0x101, 3, 3) # IOCTL_SET_MODE
INFO_IOCTRL = CTL_CODE(0x22, 0x103, 3, 3)
IOCTL_REVERSE_SEARCH_QUERY = CTL_CODE(0x22, 0x104, 3, 3)

class PyMem:
    FIELDS = (["CR3", "NtBuildNumber", "KernBase", "KDBG"] +
              ["KPCR%02d" % i for i in range(32)] +
              ["PfnDataBase", "PsLoadedModuleList", "PsActiveProcessHead"] +
              ["Padding%s" % i for i in range(0xff)] +
              ["NumberOfRuns"])
    
    def GetInfo(fd):
        result = win32file.DeviceIoControl(fd, INFO_IOCTRL, b"", 102400, None)
        fmt_string = "Q" * len(PyMem.FIELDS)
        memory_parameters = dict(zip(PyMem.FIELDS, struct.unpack_from(fmt_string, result)))
        for k, v in sorted(memory_parameters.items()):
            if k.startswith("Pad"):
                continue
            if not v: continue
            print("%s: \t%#08x (%s)" % (k, v, v))

    def SetMode(fd, modeset = "pte"):
        try:
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
            win32file.DeviceIoControl(fd, CTRL_IOCTRL, struct.pack("I", mode), 0, None)
            print(f"Mode has been set to {modeset}")
        except Exception as e:
            return str(e)
    
    def service_create():
        try:
            os.system(f"net stop winpmem")  # Stop any previous instance of the driver
            os.system(f"sc delete winpmem")  # Delete any previous instance of the driver
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
            driver = os.path.join(os.getcwd(), driver_path)
            hScm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CREATE_SERVICE)
            try:
                hSvc = win32service.CreateService(hScm, "winpmem", "winpmem", win32service.SERVICE_ALL_ACCESS, win32service.SERVICE_KERNEL_DRIVER, win32service.SERVICE_DEMAND_START, win32service.SERVICE_ERROR_IGNORE, driver, None, 0, None, None, None)
            except win32service.error as e:
                print(e)
                hSvc = win32service.OpenService(hScm, "winpmem", win32service.SERVICE_ALL_ACCESS)
                
            try:
                win32service.ControlService(hSvc, win32service.SERVICE_CONTROL_STOP)
            except win32service.error:
                pass

            try:
                win32service.StartService(hSvc, [])
            except win32service.error as e:
                print("%s: will try to continue" % e)

            print("WinPMEM Started")
        except Exception as e:
            print("ERROR : WinPMEM can not created. Reason : " + str(e))

    @staticmethod
    def dump_and_save_memory(filename, memsize = int(1024 * 1024)):
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
        if device_handle is True:
            print("Error: open device failed.\n")
        else:
            PyMem.SetMode(device_handle)
            PyMem.GetInfo(device_handle)
            print("\nMEMSIZE : " + str(memsize))
            with open(filename + ".aff", "wb") as f:
                mem_addr = 0
                while mem_addr < memsize:
                    win32file.SetFilePointer(device_handle, mem_addr, 0) # Setting pointer
                    data = win32file.ReadFile(device_handle, memsize)[1] # Reading memory...
                    f.write(data) # Writing to file
                    mem_addr += memsize
                    offset_in_mb = mem_addr / 1024 / 1024
                    if not offset_in_mb % 50:
                        sys.stdout.write("\n%04dMB\t" % offset_in_mb)
                    sys.stdout.flush()
                    print(f"Dumped {mem_addr} / {memsize} bytes and {offset_in_mb} MB/offset ({mem_addr * 100 / memsize:.2f}%)")
                f.close()
                win32file.CloseHandle(device_handle)