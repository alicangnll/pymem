import argparse
from src.pymem_class import PyMem

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PyMem memory dump example with selectable scan strategy")
    parser.add_argument("--scan", dest="scan", default="auto", choices=[
        "auto", "smart", "comprehensive", "scan", "aggressive", "fast", "ultrafast", "ultra", "ufast"
    ], help="Scan strategy to use when driver memory runs are unavailable")
    parser.add_argument("--filename", dest="filename", default="volatility_memory_dump", help="Base filename for output (no extension)")
    parser.add_argument("--memsize", dest="memsize", type=int, default=None, help="Limit dump size in bytes (default: auto-detect total RAM)")

    args = parser.parse_args()

    PyMem.service_create()
    # Drivers: https://github.com/Velocidex/WinPmem/tree/master/kernel/binaries
    # Run "bcdedit /set testsigning on" command
    # Check Memory Compression with "Get-MMAgent" command
    # Disable Memory Compression with "Disable-MMAgent -mc" command
    # Restart computer
    
    # Dump with chosen scan strategy
    if args.memsize is None:
        PyMem.dump_and_save_memory(args.filename, scan_strategy=args.scan)
    else:
        PyMem.dump_and_save_memory(args.filename, memsize=args.memsize, scan_strategy=args.scan)