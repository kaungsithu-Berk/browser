import sys
import inspect
import heapq
import random
import io

def raiseNotDefined():
    fileName = inspect.stack()[1][1]
    line = inspect.stack()[1][2]
    method = inspect.stack()[1][3]

    print("*** Method not implemented: %s at line %s of %s" %
          (method, line, fileName))
    sys.exit(1)

def combineFunctions(*funcs):
    
    def inner(*args, **kwargs):
        for f in funcs:
            f(*args, **kwargs)
            
    return inner
    



    