from transfer.transferutil import *

if __name__ == "__main__":
    import sys
    while(True):
        url = input("Enter url: ")
        if url == "exit":
            break
        
        print(get(url).getRawBody())
