#########################################################################################################
# Nelli Kemi
# 22.4.2022
# Sources: Assignments 1 and 2, Wikipedia documentation, Python documentation
#########################################################################################################

from datetime import datetime
import xmlrpc.client

def add_wikipedia_note(s):
    print("\nFind the shortest path between two Wikipedia pages")
    search_term = input("Starting page (input -1 to quit): ")
    if search_term == "-1":
        return -1
    end = input("Ending page (input -1 to quit): ")
    if end == "-1":
        return -1
    print("\n..... Looking for a path .....\n")
    try:
        path = s.find_shortest_path(search_term, end)
    except Exception as e:
        print(e)
        print("Please try again later.")
        return 0

    if len(path) <= 1:
        print("Couldn't find a path.")
        print(path)
        return 0
    print(f"Found the following path of degree {len(path) - 1}:")
    for i in range(len(path)):
        if i == len(path)-1:
            print(path[i])
        else:
            print(path[i], " > ", end="")
    print('\n')
    return 0

def main():  
    s = xmlrpc.client.ServerProxy('http://localhost:8000')
    run_app = 0
    while (run_app == 0):
        run_app = add_wikipedia_note(s)
        
    print("Closing the application.")
    exit(0)

main()