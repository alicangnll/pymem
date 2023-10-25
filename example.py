from pymem_class import PyMem

if __name__ == "__main__":
    PyMem.service_create()
    PyMem.dump_and_save_memory("demo.raw")