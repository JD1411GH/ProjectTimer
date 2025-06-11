import sys
import dataset
import datetime

# database connection
db = dataset.connect('sqlite:///project-timer.db')
table = db["time_records"]


def create_task():
    project = input("Enter project name: ")
    task = input("Enter task name: ")
    start_timer(project, task)


def daily_report():
    pass


def exit():
    global db
    db.executable.close()
    sys.exit(0)


def process_user_input():
    choice = input("Enter your choice: ")
    if choice == "0":
        create_task()
    elif choice == "s":
        stop_timer()
    elif choice == "d":
        daily_report()
    elif choice == "x":
        exit()
    else:
        print("Invalid choice. Please try again.")
        process_user_input()


def show_default_options():
    print("0. New task")
    print("\n[s] Stop timer")
    print("[d] Daily report")
    print("[x] Exit")


def start_timer(project, task):
    global table
    table.insert({
        "project": project,
        "task": task,
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": None
    })


def stop_timer():
    pass


def main():
    show_default_options()
    process_user_input()


if __name__ == "__main__":
    main()
    exit()
