import ctypes
import struct
import sys
import win32file
import win32service
import os
from ctypes import *
import time
import psutil


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

    def GetMemoryRuns(fd):
        """Get memory runs from winpmem driver to identify readable memory regions"""
        try:
            result = win32file.DeviceIoControl(fd, INFO_IOCTRL, b"", 102400, None)
            fmt_string = "Q" * len(PyMem.FIELDS)
            memory_parameters = dict(zip(PyMem.FIELDS, struct.unpack_from(fmt_string, result)))
            
            # Get the number of runs
            number_of_runs = memory_parameters.get("NumberOfRuns", 0)
            if number_of_runs == 0:
                print("No memory runs found")
                return []
            
            print(f"Found {number_of_runs} memory runs")
            
            # Read memory runs data
            runs_data_size = number_of_runs * 16  # Each run is 16 bytes (2 QWORDs)
            runs_data = win32file.DeviceIoControl(fd, INFO_IOCTRL, b"", runs_data_size + 102400, None)
            
            # Parse memory runs (start_address, length)
            runs = []
            for i in range(number_of_runs):
                start_addr = struct.unpack_from("Q", runs_data, 102400 + i * 16)[0]
                length = struct.unpack_from("Q", runs_data, 102400 + i * 16 + 8)[0]
                runs.append((start_addr, length))
                print(f"Run {i+1}: Start=0x{start_addr:016x}, Length=0x{length:016x} ({length/1024/1024:.2f} MB)")
            
            return runs
        except Exception as e:
            print(f"Error getting memory runs: {e}")
            return []

    def GetSystemRAMSize():
        """Get total system RAM size in bytes"""
        try:
            # Get total physical memory
            total_memory = psutil.virtual_memory().total
            print(f"Total system RAM detected: {total_memory / 1024 / 1024 / 1024:.2f} GB")
            return total_memory
        except Exception as e:
            print(f"Error detecting RAM size: {e}")
            # Fallback to 8GB if detection fails
            fallback_size = 8 * 1024 * 1024 * 1024
            print(f"Using fallback size: {fallback_size / 1024 / 1024 / 1024:.2f} GB")
            return fallback_size

    def GetKnownSafeRegions():
        """Return known safe memory regions based on Windows memory layout"""
        # These are typically safe physical memory regions on Windows systems
        safe_regions = [
            # Low memory region (0-16MB) - usually safe
            (0x00000000, 16 * 1024 * 1024),
            # Common kernel region (around 1GB mark)
            (0x40000000, 64 * 1024 * 1024),
            # Another common safe region
            (0x80000000, 128 * 1024 * 1024),
        ]
        return safe_regions

    def ScanMemoryRegions(fd, max_size=32*1024*1024*1024):
        """Scan memory regions more comprehensively to find all readable areas"""
        print("Scanning memory regions comprehensively...")
        safe_regions = []
        chunk_size = 4 * 1024 * 1024  # 4MB chunks for faster scanning
        current_addr = 0
        consecutive_failures = 0
        max_consecutive_failures = 30  # Allow more failures before stopping
        
        print(f"Scanning up to {max_size/1024/1024/1024:.2f} GB of memory...")
        print("=" * 50)
        
        while current_addr < max_size and consecutive_failures < max_consecutive_failures:
            # Test if this region is readable
            is_readable, _ = PyMem.TestMemoryRead(fd, current_addr, min(4096, chunk_size))
            
            if is_readable:
                # Found a readable region, try to determine its size
                region_start = current_addr
                region_size = 0
                
                # Test different sizes to find the maximum readable chunk
                test_sizes = [chunk_size, chunk_size//2, chunk_size//4, 1024*1024, 256*1024, 64*1024]
                
                for test_size in test_sizes:
                    if test_size > max_size - current_addr:
                        test_size = max_size - current_addr
                    
                    try:
                        win32file.SetFilePointer(fd, current_addr, 0)
                        data = win32file.ReadFile(fd, test_size)[1]
                        if len(data) == test_size:
                            region_size = test_size
                            break
                    except:
                        continue
                
                if region_size > 0:
                    safe_regions.append((region_start, region_size))
                    print(f"Safe region found: 0x{region_start:016x} - 0x{region_start + region_size:016x} ({region_size/1024/1024:.2f} MB)")
                    current_addr += region_size
                    consecutive_failures = 0
                else:
                    current_addr += chunk_size
                    consecutive_failures += 1
            else:
                # Skip this region
                current_addr += chunk_size
                consecutive_failures += 1
                
            # Progress update every 500MB with percentage and visual bar
            if not int(current_addr / 1024 / 1024 / 512) % 1:
                progress_percent = (current_addr / max_size) * 100
                bar_length = 30
                filled_length = int(bar_length * current_addr // max_size)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                print(f"Scan progress: [{bar}] {progress_percent:.1f}% ({current_addr / 1024 / 1024:.0f} MB)")
        
        print(f"Memory scan completed. Found {len(safe_regions)} safe regions")
        total_safe_size = sum(region[1] for region in safe_regions)
        print(f"Total safe memory: {total_safe_size / 1024 / 1024:.2f} MB")
        
        return safe_regions

    def AggressiveMemoryScan(fd, max_size=32*1024*1024*1024):
        """More aggressive memory scanning to find all possible readable regions"""
        print("Performing aggressive memory scan...")
        safe_regions = []
        chunk_size = 8 * 1024 * 1024  # 8MB chunks for faster aggressive scanning
        current_addr = 0
        consecutive_failures = 0
        max_consecutive_failures = 100  # Allow many more failures
        
        print(f"Aggressively scanning up to {max_size/1024/1024/1024:.2f} GB of memory...")
        
        while current_addr < max_size and consecutive_failures < max_consecutive_failures:
            # Try to read this region
            region_start = current_addr
            region_size = 0
            
            # Try different chunk sizes from large to small
            test_sizes = [chunk_size, chunk_size//2, chunk_size//4, 2*1024*1024, 1024*1024, 256*1024, 64*1024]
            
            for test_size in test_sizes:
                if test_size > max_size - current_addr:
                    test_size = max_size - current_addr
                if test_size < 4096:  # Minimum viable size
                    break
                    
                try:
                    win32file.SetFilePointer(fd, current_addr, 0)
                    data = win32file.ReadFile(fd, test_size)[1]
                    if len(data) > 0:  # Accept any data, even partial reads
                        region_size = len(data)
                        break
                except:
                    continue
            
            if region_size > 0:
                safe_regions.append((region_start, region_size))
                print(f"Readable region: 0x{region_start:016x} - 0x{region_start + region_size:016x} ({region_size/1024/1024:.2f} MB)")
                current_addr += region_size
                consecutive_failures = 0
            else:
                # Skip this region
                current_addr += chunk_size
                consecutive_failures += 1
                
            # Progress update every 500MB with percentage and visual bar
            if not int(current_addr / 1024 / 1024 / 512) % 1:
                progress_percent = (current_addr / max_size) * 100
                bar_length = 30
                filled_length = int(bar_length * current_addr // max_size)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                print(f"Aggressive scan: [{bar}] {progress_percent:.1f}% ({current_addr / 1024 / 1024:.0f} MB)")
        
        print(f"Aggressive scan completed. Found {len(safe_regions)} readable regions")
        total_readable_size = sum(region[1] for region in safe_regions)
        print(f"Total readable memory: {total_readable_size / 1024 / 1024:.2f} MB")
        
        return safe_regions

    def FastMemoryScan(fd, max_size=32*1024*1024*1024):
        """Very fast memory scanning using large chunks"""
        print("Performing fast memory scan...")
        safe_regions = []
        chunk_size = 32 * 1024 * 1024  # 32MB chunks for very fast scanning
        current_addr = 0
        consecutive_failures = 0
        max_consecutive_failures = 200  # Allow many failures
        
        print(f"Fast scanning up to {max_size/1024/1024/1024:.2f} GB of memory...")
        
        while current_addr < max_size and consecutive_failures < max_consecutive_failures:
            # Try to read this region
            region_start = current_addr
            region_size = 0
            
            # Try only large chunks for speed
            test_sizes = [chunk_size, chunk_size//2, 8*1024*1024, 2*1024*1024]
            
            for test_size in test_sizes:
                if test_size > max_size - current_addr:
                    test_size = max_size - current_addr
                if test_size < 1024*1024:  # Minimum 1MB
                    break
                    
                try:
                    win32file.SetFilePointer(fd, current_addr, 0)
                    data = win32file.ReadFile(fd, test_size)[1]
                    if len(data) > 0:  # Accept any data
                        region_size = len(data)
                        break
                except:
                    continue
            
            if region_size > 0:
                safe_regions.append((region_start, region_size))
                print(f"Fast region: 0x{region_start:016x} - 0x{region_start + region_size:016x} ({region_size/1024/1024:.2f} MB)")
                current_addr += region_size
                consecutive_failures = 0
            else:
                # Skip this region
                current_addr += chunk_size
                consecutive_failures += 1
                
            # Progress update every 1GB with percentage and visual bar
            if not int(current_addr / 1024 / 1024 / 1024) % 1:
                progress_percent = (current_addr / max_size) * 100
                bar_length = 30
                filled_length = int(bar_length * current_addr // max_size)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                print(f"Fast scan: [{bar}] {progress_percent:.1f}% ({current_addr / 1024 / 1024 / 1024:.1f} GB)")
        
        print(f"Fast scan completed. Found {len(safe_regions)} readable regions")
        total_readable_size = sum(region[1] for region in safe_regions)
        print(f"Total readable memory: {total_readable_size / 1024 / 1024:.2f} MB")
        
        return safe_regions

    def TestMemoryRead(fd, address, size=4096):
        """Test if a memory address is readable"""
        try:
            win32file.SetFilePointer(fd, address, 0)
            data = win32file.ReadFile(fd, size)[1]
            return True, data
        except Exception as e:
            return False, None

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
    def dump_and_save_memory(filename, memsize = None):
        # Auto-detect RAM size if not provided
        if memsize is None:
            print("Auto-detecting system RAM size...")
            memsize = PyMem.GetSystemRAMSize()
        else:
            print(f"Using specified memory size: {memsize / 1024 / 1024 / 1024:.2f} GB")
        
        print("Creating AFF4 (Rekall) file")
        device_handle = win32file.CreateFile(
            "\\\\.\\pmem",
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
            None,
            win32file.OPEN_EXISTING,
            win32file.FILE_ATTRIBUTE_NORMAL,
            None)
        
        if device_handle == -1:
            print("Error: open device failed.\n")
            return
        
        try:
            # Try different modes for better compatibility
            print("Trying different winpmem modes...")
            for mode in ["pte", "physical", "iospace"]:
                try:
                    print(f"Testing mode: {mode}")
                    PyMem.SetMode(device_handle, mode)
                    PyMem.GetInfo(device_handle)
                    print(f"Mode {mode} successful!")
                    break
                except Exception as e:
                    print(f"Mode {mode} failed: {e}")
                    continue
            
            # Get memory runs to identify readable regions
            print("\nDetecting readable memory regions...")
            memory_runs = PyMem.GetMemoryRuns(device_handle)
            
            if not memory_runs:
                print("No valid memory runs found. Performing comprehensive memory scan...")
                memory_runs = PyMem.ScanMemoryRegions(device_handle, memsize)
                
                if not memory_runs:
                    print("No safe memory regions found. Trying aggressive scan...")
                    memory_runs = PyMem.AggressiveMemoryScan(device_handle, memsize)
                    
                    if not memory_runs:
                        print("No readable memory found. Trying fast scan...")
                        memory_runs = PyMem.FastMemoryScan(device_handle, memsize)
                        
                        if not memory_runs:
                            print("No readable memory found. Aborting dump to prevent system crash.")
                            return
            
            print(f"\nTotal memory runs: {len(memory_runs)}")
            total_readable_size = sum(run[1] for run in memory_runs)
            print(f"Total readable memory: {total_readable_size / 1024 / 1024:.2f} MB")
            
            with open(filename + ".aff", "wb") as f:
                total_dumped = 0
                for i, (start_addr, length) in enumerate(memory_runs):
                    print(f"\nProcessing run {i+1}/{len(memory_runs)}: 0x{start_addr:016x} - 0x{start_addr + length:016x}")
                    
                    # Balanced reading with reasonable chunks
                    chunk_size = min(1024 * 1024, length)  # 1MB chunks - good balance of speed and safety
                    current_addr = start_addr
                    remaining = length
                    consecutive_errors = 0
                    max_consecutive_errors = 5  # Reasonable error limit
                    
                    print(f"Reading region in 1MB chunks...")
                    
                    while remaining > 0 and consecutive_errors < max_consecutive_errors:
                        read_size = min(chunk_size, remaining)
                        
                        try:
                            # Triple safety check
                            win32file.SetFilePointer(device_handle, current_addr, 0)
                            
                            # Read with timeout protection
                            data = win32file.ReadFile(device_handle, read_size)[1]
                            
                            if len(data) == 0:
                                print(f"No data at 0x{current_addr:016x}, skipping...")
                                remaining -= read_size
                                current_addr += read_size
                                consecutive_errors += 1
                                continue
                            
                            # Verify we got the expected amount of data
                            if len(data) != read_size:
                                print(f"Partial read at 0x{current_addr:016x}: got {len(data)} bytes, expected {read_size}")
                                remaining -= len(data)
                                current_addr += len(data)
                                consecutive_errors += 1
                                continue
                            
                            f.write(data)
                            
                            total_dumped += len(data)
                            remaining -= len(data)
                            current_addr += len(data)
                            consecutive_errors = 0  # Reset error counter on success
                            
                            # Progress reporting every 1MB with percentage and visual bar
                            progress_mb = total_dumped / 1024 / 1024
                            if not int(progress_mb) % 1:  # Report every 1MB
                                progress_percent = (total_dumped / memsize) * 100
                                bar_length = 30
                                filled_length = int(bar_length * total_dumped // memsize)
                                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                                print(f"Dump: [{bar}] {progress_percent:.1f}% ({progress_mb:.0f} MB)")
                            
                        except Exception as e:
                            print(f"Error reading at 0x{current_addr:016x}: {e}")
                            consecutive_errors += 1
                            # Skip this chunk and continue
                            remaining -= read_size
                            current_addr += read_size
                            
                            # If too many consecutive errors, skip this region entirely
                            if consecutive_errors >= max_consecutive_errors:
                                print(f"Too many consecutive errors in region, skipping remaining {remaining/1024/1024:.2f} MB")
                                break
                            continue
                    
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"Region 0x{start_addr:016x} had too many errors, moving to next region...")
                
                print(f"\nDump completed. Total dumped: {total_dumped / 1024 / 1024:.2f} MB")
                
        finally:
            win32file.CloseHandle(device_handle)

    @staticmethod
    def _dump_sequential_safe(device_handle, filename, memsize):
        """Fallback method for sequential dumping with safety checks"""
        print(f"Sequential dump with safety checks. Target size: {memsize / 1024 / 1024:.2f} MB")
        
        chunk_size = 64 * 1024  # 64KB chunks for safety
        total_dumped = 0
        
        with open(filename + ".aff", "wb") as f:
            current_addr = 0
            
            while current_addr < memsize and total_dumped < memsize:
                remaining = min(chunk_size, memsize - current_addr)
                
                # Test if this chunk is readable
                is_readable, data = PyMem.TestMemoryRead(device_handle, current_addr, min(4096, remaining))
                
                if is_readable:
                    try:
                        win32file.SetFilePointer(device_handle, current_addr, 0)
                        data = win32file.ReadFile(device_handle, remaining)[1]
                        f.write(data)
                        total_dumped += len(data)
                        current_addr += len(data)
                        
                        if not int(total_dumped / 1024 / 1024) % 50:
                            print(f"Progress: {total_dumped / 1024 / 1024:.0f} MB dumped")
                            
                    except Exception as e:
                        print(f"Error reading at 0x{current_addr:016x}: {e}")
                        # Skip this chunk
                        current_addr += remaining
                else:
                    # Skip unreadable region
                    current_addr += remaining
                    print(f"Skipping unreadable region at 0x{current_addr:016x}")
        
        print(f"Sequential dump completed. Total dumped: {total_dumped / 1024 / 1024:.2f} MB")

    @staticmethod
    def test_memory_safety(filename="test", test_size=100*1024*1024):
        """Test memory dumping with a small amount first"""
        print(f"Testing memory safety with {test_size/1024/1024:.0f} MB dump...")
        PyMem.dump_and_save_memory(filename, test_size)

    @staticmethod
    def dump_full_memory(filename="memory_dump"):
        """Dump entire system memory automatically"""
        print("=== FULL MEMORY DUMP ===")
        print("Auto-detecting system RAM and creating full memory dump...")
        PyMem.dump_and_save_memory(filename)