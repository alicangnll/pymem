
import os, sys
from pymem_snaphot import PyMemSnapshot


if os.name == "nt":
    name = input("Memory image name : ")
    if name == "" or name is None:
        print("FATAL ERROR : IMAGE CAN NOT GET!")
    else:
        PyMemSnapshot.get_memimg_win(str(name))  
else:
    print("FATAL ERROR : OS ARE NOT SUPPORTING!")
    sys.exit(0)