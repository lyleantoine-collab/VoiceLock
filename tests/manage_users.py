# tests/manage_users.py
from modules.voicelock import enroll, list_users, delete_user

print("1. Enroll | 2. List | 3. Delete")
choice = input("Choose: ")

if choice == "1":
    name = input("Name: ")
    enroll(name)
elif choice == "2":
    list_users()
elif choice == "3":
    name = input("Delete: ")
    delete_user(name)
