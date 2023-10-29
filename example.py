from src.pymem_class import PyMem

if __name__ == "__main__":
    PyMem.service_create()
    # Drivers: https://github.com/Velocidex/WinPmem/tree/master/kernel/binaries
    # Run "bcdedit /set testsigning on" command
    # Check Memory Compression with "Get-MMAgent" command
    # Disable Memory Compression with "Disable-MMAgent -mc" command
    # Restart computer
    PyMem.dump_and_save_memory("demo")