# PyMem - Windows Memory Acquisition Tool

A Python-based Windows memory acquisition tool that creates Volatility-compatible raw memory dumps. Uses the WinPMEM driver to safely read physical memory with multiple scanning strategies for optimal performance across different system configurations.

## Key Features

- **Volatility Compatible**: Creates raw memory dumps that work directly with Volatility 2/3
- **Smart Memory Scanning**: Multiple scan strategies (smart, fast, ultra-fast) with adaptive chunk sizing
- **MMIO Region Skipping**: Automatically skips known problematic memory regions
- **Large Memory Support**: Handles systems with 32GB+ RAM efficiently
- **Progress Tracking**: Real-time progress bars and detailed logging
- **CLI Interface**: Command-line options for scan strategy and output control

## How It Works

PyMem automatically detects your system's RAM size and uses adaptive chunk sizing based on total memory. It employs multiple scanning strategies to find readable memory regions, skipping known problematic areas like MMIO regions. The tool creates a raw memory dump with physical memory layout preserved for Volatility analysis.

## Compatible Analysis Tools

- **Volatility 2**: `python vol.py -f memory_dump.raw imageinfo`
- **Volatility 3**: `vol -f memory_dump.raw windows.info`
- **AccessData FTK Imager**: Raw memory analysis
- **Rekall**: Memory forensics framework

## Tested Operating Systems

- Windows 11 Build Number 22621.2283 (Virtual Machine)

## Screenshots

![FTK Imager Test](pic/ftk_imager_test.png)

![Windows Test](pic/wintest.png)

## Installation & Setup

### Prerequisites

1. **Enable Test Signing** (Administrator required):
   ```cmd
   bcdedit /set testsigning on
   ```

2. **Check Memory Compression**:
   ```powershell
   Get-MMAgent
   ```

3. **Disable Memory Compression** (recommended for better performance):
   ```powershell
   Disable-MMAgent -mc
   ```

4. **Restart your computer**

### Installation

```bash
# Install Python dependencies
winget install python
python -m pip install -r requirements.txt

# Or install from PyPI
pip install pymem_snapshot
```

## Usage Examples

### Basic Usage

```bash
# Auto-detect RAM, use smart scan (default)
python example.py

# Custom filename
python example.py --filename my_memory_dump

# Limit memory size (4GB example)
python example.py --memsize 4294967296 --filename limited_dump
```

### Scan Strategies

```bash
# Fast scan for large systems (16GB+)
python example.py --scan fast --filename fast_dump

# Ultra-fast scan for very large systems (32GB+)
python example.py --scan ultrafast --filename ultra_dump

# Comprehensive scan for thorough analysis
python example.py --scan comprehensive --filename deep_analysis

# Aggressive scan for problematic systems
python example.py --scan aggressive --filename aggressive_dump
```

### Available Scan Strategies

| Strategy | Use Case | Speed | Coverage | Best For |
|----------|----------|-------|----------|----------|
| `smart` | Default choice | Fast | High | Most systems |
| `fast` | Large systems | Very Fast | Good | 16GB+ RAM |
| `ultrafast` | Very large systems | Fastest | Good | 32GB+ RAM |
| `comprehensive` | Thorough analysis | Slow | Highest | Critical analysis |
| `aggressive` | Problematic systems | Medium | Very High | Troubleshooting |

## Output Files

- **`filename.raw`**: Raw memory dump (Volatility-compatible)
- **`filename_metadata.json`**: Memory runs and system information
- **`filename_volatility_info.txt`**: Volatility commands and analysis guide

## Performance Notes

- **32GB+ Systems**: Use `--scan ultrafast` for best performance
- **Memory Compression**: Disable with `Disable-MMAgent -mc` for better results
- **Disk Space**: Ensure 1.5x RAM size free space (e.g., 48GB for 32GB RAM)
- **Antivirus**: Temporarily disable real-time scanning during acquisition
- **NTFS Required**: FAT32 has 4GB file size limit

## Volatility Analysis

After creating a memory dump, analyze it with Volatility:

### Volatility 2
```bash
python vol.py -f memory_dump.raw imageinfo
python vol.py -f memory_dump.raw --profile=Win10x64 pslist
python vol.py -f memory_dump.raw --profile=Win10x64 pstree
python vol.py -f memory_dump.raw --profile=Win10x64 cmdline
```

### Volatility 3
```bash
vol -f memory_dump.raw windows.info
vol -f memory_dump.raw windows.pslist
vol -f memory_dump.raw windows.pstree
vol -f memory_dump.raw windows.cmdline
```

## API Usage

```python
from src.pymem_class import PyMem

# Create service and dump with smart scan
PyMem.service_create()
PyMem.dump_and_save_memory("my_dump", scan_strategy="smart")

# Dump with custom memory size
PyMem.dump_and_save_memory("limited_dump", 
                          memsize=4*1024*1024*1024,  # 4GB
                          scan_strategy="fast")

# Volatility-compatible dump
PyMem.dump_volatility_compatible("vol_dump")
```

## Troubleshooting

### Common Issues

1. **"Driver file not found"**: Ensure `winpmem_x64.sys` or `winpmem_x86.sys` is in the project directory
2. **"Access denied"**: Run as Administrator
3. **"Test signing not enabled"**: Run `bcdedit /set testsigning on` and restart
4. **Slow scanning**: Try `--scan ultrafast` for large systems
5. **Memory compression issues**: Disable with `Disable-MMAgent -mc`

### Performance Optimization

- Use SSD storage for faster I/O
- Disable Windows Defender real-time protection during acquisition
- Close unnecessary applications to free memory
- Use `--scan ultrafast` for systems with 32GB+ RAM

## Disclaimer

**WARNING**: Memory acquisition is a critical process that can cause system instability, BSODs, or data corruption. Always test in isolated environments first. The authors are not responsible for any system damage or data loss.

**UYARI**: Bellek imajı alma kritik bir süreçtir ve sistem kararsızlığına, BSOD'lara veya veri bozulmasına neden olabilir. Her zaman önce izole ortamlarda test edin. Yazarlar herhangi bir sistem hasarı veya veri kaybından sorumlu değildir.

## Links

- [PyPI Package](https://pypi.org/project/pymem-snapshot/)
- [WinPMEM Driver](https://github.com/Velocidex/WinPmem)

## Credits

Great thanks to the [Velocidex (WinPMEM)](https://github.com/Velocidex/WinPmem) team for providing the kernel drivers.

## License

See [LICENSE](LICENSE) file for details.