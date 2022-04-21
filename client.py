#########################################################################################################
# Nelli Kemi
# 23.3.2022
#########################################################################################################

from datetime import datetime
import xmlrpc.client


def menu():
    print("\nWhat would you like to do?")
    print("1) Add a new note")
    print("2) Browse through your notebook")
    print("3) Add a Wikipedia reference to an existing topic")
    print("4) Quit")

def add_wikipedia_note():
    search_term = input("Search terms for looking up data on Wikipedia: ")
    end = input("End term: ")
    try:
        error = s.search_wikipedia(search_term, end)
    except Exception as e:
        print(e)
        print("Please try again later.")
        return

    if error != "":
        print(error)
    else:
        print(f"Note referencing Wikipedia added to topic {topic}")

s = xmlrpc.client.ServerProxy('http://localhost:8000')
choice = "-1"
while (choice != "0"):
    menu()
    choice = input("Your choice: ")
    if choice == "3":
        add_wikipedia_note()
    elif choice == "4":
        break
    else:
        print("Invalid choice. Please try again.")

print("Thank you for using the notebook.")
exit(0)