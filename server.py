#########################################################################################################
# Nelli Kemi
# 22.4.2022
# Sources: Assignments 1 and 2, Wikipedia documentation, Python documentation
#########################################################################################################

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
from threading import Thread, Lock
import wikipedia

lock = Lock()
# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def search_wikipedia(search_terms, paths_list, visited_pages, success, end):
    if len(visited_pages) == 0:
        try:
            checked_end = wikipedia.search(end[0], results=1)
            end.clear()
            end.extend(checked_end)
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Choose first option when multiple pages are available
            checked_end = wikipedia.search(e.options[0], results=1)
            end.clear()
            end.extend(checked_end)

    found = []
    for search in search_terms:
        try:
            try:
                # Look up last page on the path
                title = wikipedia.search(search[-1], results=1)
            except wikipedia.exceptions.DisambiguationError as e:
                # Choose first option when multiple pages are available
                title = wikipedia.search(e.options[0], results=1)
                
            try:
                result = wikipedia.page(title[0], auto_suggest=False)
            except wikipedia.exceptions.DisambiguationError as e:
                # Choose first option when multiple pages are available
                result = wikipedia.page(e.options[0], auto_suggest=False)
        except:
            # some other error occured, skip this title and look for the next
            continue
        
        for link in result.links:
            if link not in visited_pages:  
                if len(success) != 0:
                    # a shortest path has been found, return to main worker
                    return 0
                if link == end[0]:
                    found = search.copy()
                    found.append(link)
                    break
                # Acquire lock to make sure no other child worker is modifying the resource at the same time
                lock.acquire()
                visited_pages.append(link)
                new_path = search.copy()
                new_path.append(link)
                paths_list.append(new_path)
                lock.release()
        
        if len(found) != 0 and len(success) == 0:
            # Acquire lock to make sure no other child worker is modifying the resource at the same time
            lock.acquire()
            success.extend(found)
            lock.release()
            break

        if len(success) != 0:
            break
        
    
with SimpleXMLRPCServer(('localhost', 8000), requestHandler=RequestHandler) as server:
    server.register_introspection_functions()
    
    def find_shortest_path(search_term, final_page):
        paths = []
        success = []
        visited_pages = []
        end = [final_page]
        degree = 1

        print("Looking for", degree, "degree paths")

        t1 = Thread(target=search_wikipedia, args=([[search_term]], paths, visited_pages, success, end))
        t1.start()
        # wait for first thread to terminate before moving forward
        t1.join()
        
        # if path was already found, send response to client
        if len(success) != 0 :
            return success

        i = 0
        threads = []
        degree += 1
        while len(success) == 0 :
            print("Looking for", degree, "degree paths")
            print(len(paths), "paths to go through")
            new_paths = []
            # create 20 child workers and give each a portion of the links to go through
            for i in range(20):
                # divide paths equally for each child
                start = i*round(len(paths)/20)
                if i < 19:
                    ending = start + round(len(paths)/20)
                else:
                    ending = None
                threads.append(Thread(target=search_wikipedia, args=(paths[start:ending], new_paths, visited_pages, success, end)))
                
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Remove threads from list to be able to start new threads during the next round
            while len(threads) != 0:
                for thread in threads:
                    if not thread.is_alive():
                        threads.remove(thread)

            paths.clear()
            
            if len(new_paths) == 0:
                success = ["Could not find more paths to explore."]
                break

            paths = new_paths.copy()
            new_paths.clear()
            i = 0
            degree += 1

        return success
    server.register_function(find_shortest_path, "find_shortest_path")  

    # Run server's main loop
    server.serve_forever()