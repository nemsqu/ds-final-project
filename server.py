#########################################################################################################
# Nelli Kemi
# 23.3.2022
#########################################################################################################

from datetime import datetime
import queue
import threading
from time import sleep
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xml.etree.ElementTree as ET
# import requests <-- doesn't work in VS code for some reason https://stackoverflow.com/questions/48775755/importing-requests-into-python-using-visual-studio-code
from pip._vendor import requests
from threading import Thread
import wikipedia

paths = []
success = []
data = {}
lock = threading.Lock()

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def search_wikipedia(search, path, paths_list, visited_pages):
    title = wikipedia.search(search)
    print(title)
    print(title[0])
    result = wikipedia.page(title[0], auto_suggest=False)
    print(result)
    #data = result.json()
    data = result.links
    for link in data:
        if link not in visited_pages:
            visited_pages.append(link)
            paths_list = list(map(lambda x: x.replace(path, path.append(link))))
    print(data)
    print(paths_list)
    #paths_queue.put(data)

def search_thread(data, end, title, paths_queue):
    success = []
    paths = []
    print("starting search")
    # following looping from https://stackoverflow.com/questions/14882571/how-to-get-all-urls-in-a-wikipedia-page
    for key, val in data["query"]["pages"].items():
        for link in val["links"]:
            #print(link["title"])
            #print(end)
            if(link["title"] == end):
                #print("match")
                success.append({"path": title + " > " + link["title"], "degree": 1})
            else:
                #print("Täällä")
                paths.append({"path": title + " > " + link["title"], "next": link["title"]})
    print("first round done")
    while "continue" in data:
        print("continue found")
        plcontinue = data["continue"]["plcontinue"]
        URL = "https://en.wikipedia.org/w/api.php"
        PARAMS = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "links",
            "pllimit": "max",
            "plcontinue": plcontinue
        }

        result = requests.get(url=URL, params=PARAMS)
        data = result.json()
        #print(data)
        for key, val in data["query"]["pages"].items():
            if "links" in val:
                for link in val["links"]:
                    #print(link["title"])
                    #print(end)
                    if(link["title"] == end):
                        #print("match")
                        success.append({"path": title + " > " + link["title"], "degree": 1})
                    else:
                        print("Täällä")
                        paths.append({"path": title + " > " + link["title"], "next": link["title"]})
    paths_queue.put({"success": success, "paths": paths})
    print(len(paths))
    print("done here too")
        #paths_queue.task_done()
        #paths_queue.put(paths)

def search_thread_higher(end, old_paths, success_list, paths_list, i):
    success = []
    paths = []
    print("Old paths ", len(old_paths))
    for item in old_paths:
        URL = "https://en.wikipedia.org/w/api.php"
        PARAMS = {
            "action": "query",
            "format": "json",
            "titles": item["next"],
            "prop": "links",
            "pllimit": "max"
        }

        result = requests.get(url=URL, params=PARAMS)
        try:
            data = result.json()
            # following looping from https://stackoverflow.com/questions/14882571/how-to-get-all-urls-in-a-wikipedia-page
            for key, val in data["query"]["pages"].items():
                if "links" in val:
                    for link in val["links"]:
                        #print(link["title"])
                        #print(end)
                        if(link["title"] == end):
                            #print("match")
                            success.append({"path": item["path"] + " > " + link["title"], "degree": 1})
                        else:
                            #print("Täällä")
                            paths.append({"path": item["path"] + " > " + link["title"], "next": link["title"]})
        except:
            print(result)
        while "continue" in data:
            plcontinue = data["continue"]["plcontinue"]
            URL = "https://en.wikipedia.org/w/api.php"
            PARAMS = {
                "action": "query",
                "format": "json",
                "titles": item["next"],
                "prop": "links",
                "pllimit": "max",
                "plcontinue": plcontinue
            }

            result = requests.get(url=URL, params=PARAMS)
            try:
                data = result.json()
            except:
                print(result)
                continue
            #print(data)
            for key, val in data["query"]["pages"].items():
                if "links" in val:
                    for link in val["links"]:
                        #print(link["title"])
                        #print(end)
                        if(link["title"] == end):
                            #print("match")
                            success.append({"path": item["path"] + " > " + link["title"], "degree": 1})
                        else:
                            #print("Täällä")
                            paths.append({"path": item["path"] + " > " + link["title"], "next": link["title"]})
            #paths_queue.put({"success": success, "paths": paths})
    lock.acquire()
    print("pahts ", len(paths), " in ", i)
    paths_list.extend(paths)
    success_list.extend(success)
    lock.release()
            #print(paths_list)
            #paths_queue.task_done()
            #paths_queue.put(paths)
    
with SimpleXMLRPCServer(('localhost', 8000), requestHandler=RequestHandler) as server:
    server.register_introspection_functions()
    
    def add_wikipedia_notes(search_term, end):
        paths_queue = queue.Queue()
        t1 = Thread(target=search_wikipedia, args=(search_term, paths_queue))
        t1.start()
        while t1.is_alive():
            sleep(0.1)
        data = paths_queue.get()
        print(data)
        print("data done, serach_thread next")
        if(data):
            return data
        
        t2 = Thread(target=search_thread, args=(data, end, search_term, paths_queue))
        t2.start()
        while t2.is_alive():
            sleep(0.1)
        print("DONE")
        queue_data = paths_queue.get(True, 60)
        paths = queue_data["paths"]
        success = queue_data["success"]
        #print(paths)
        #print(success)
        
        if len(success) != 0 :
            return success
        #second_degree_paths = []
        i = 0
        threads = []
        #muokkaa tätä niin, että vaan x määrä threadejä luodaan
        while len(success) == 0 :
            print("starting round")
            print(len(paths))
            new_paths = []
            for i in range(20):
                #print(i)
                start = i*round(len(paths)/20)
                if i < 19:
                    ending = start + round(len(paths)/20)
                else:
                    ending = None
                threads.append(Thread(target=search_thread_higher, args=(end, paths[start:ending], success, new_paths, i)))
                #print("DONE")
                #i = i + 1
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            paths.clear()
            #queue_data = paths_queue.get(True, 60)
            print("after get")
            #print(new_paths)
            if len(new_paths) == 0:
                break
            #paths.append(queue_data["paths"])
            #if len(queue_data["success"]) != 0:
            #    success.append(queue_data["success"])
            print("success: ")
            print(success)
            #paths = paths_queue.get()
            #paths = list(filter(lambda i: i['path'] == item['path'], paths))
            
            paths = new_paths.copy()
            new_paths.clear()
            print(len(threads))
            while len(threads) != 0:
                for thread in threads:
                    if not thread.is_alive():
                        threads.remove(thread)
            print(len(threads))
            i = 0
                #if len(success) != 0 :
                #    return success
            """ data = search_wikipedia(item["next"])
                #print(data)
            for key, val in data["query"]["pages"].items():
                if "links" in val:
                    for link in val["links"]:
                        #print(link["title"])
                        if(link["title"] == end):
                            #print("match")
                            success.append({"path": item["path"] + " > " + link["title"], "degree": 2})
                        else:
                        #print("Täällä")
                            page_titles.append(link["title"])
                            paths.append({"path": item["path"] + " > " + link["title"], "next": link["title"]})
            while "continue" in data:
                plcontinue = data["continue"]["plcontinue"]
                URL = "https://en.wikipedia.org/w/api.php"
                PARAMS = {
                    "action": "query",
                    "format": "json",
                    "titles": item["next"],
                    "prop": "links",
                    "pllimit": "max",
                    "plcontinue": plcontinue
                }

                result = requests.get(url=URL, params=PARAMS)
                data = result.json()
                #print(data["query"]["pages"].items())
                for key, val in data["query"]["pages"].items():
                    print(val)
                    print("\n")
                    if "links" in val:
                        for link in val["links"]:
                            #print(link["title"])
                            if(link["title"] == end):
                                #print("match")
                                success.append({"path": item["path"] + " > " + link["title"], "degree": 2})
                            else:
                            #print("Täällä")
                                page_titles.append(link["title"])
                                paths.append({"path": item["path"] + " > " + link["title"], "next": link["title"]}) """
                    

        
        return success
    server.register_function(add_wikipedia_notes, "search_wikipedia")  

    # Run server's main loop
    server.serve_forever()