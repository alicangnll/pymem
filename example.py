
from pymem_snaphot import PyMemSnapshot

name = input("Memory image name (Ex: example.raw) : ") # Memory image name (Ex: example.raw)
PyMemSnapshot.get_memimg_win(str(name))  