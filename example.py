
import os
from pymem_snaphot import PyMemSnapshot

print("--------------- PyMem Capture v1 ---------------")
if os.name == "nt":
    name = input("Memory image name : ")
    if name == "" or name is None:
        print("FATAL ERROR : IMAGE CAN NOT GET!")
    else:
        try:
            print("--------------- MEMORY SNAPSHOTTING PLEASE WAIT ---------------")
            PyMemSnapshot.get_memimg_win(str(name))
        except Exception as e:
            print("FATAL ERROR : IMAGE CAN NOT GET\nREASON : " + str(e))
else:
    print("FATAL ERROR : THAT SYSTEMS ARE NOT SUPPORTING!")
