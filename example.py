from pymem_class import PyMem

if __name__ == "__main__":
    PyMem.service_create()
    # Run "bcdedit /set testsigning on" command
    # Check Memory Compression with "Get-MMAgent" command
    # Disable Memory Compression with "Disable-MMAgent -mc" command
    # Restart computer
    memsize = 1024 * 1024 # 1 MB Image
    PyMem.dump_and_save_memory("demo", memsize)