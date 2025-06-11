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
    print("[t] Task report")
    print("[x] Exit")


def show_project_list():
    global table

    # Project list
    projects = [{"project": row['project']}
                for row in table.distinct('project')]

    # effort spent
    today = datetime.date.today()
    today_records = [
        row for row in table.all()
        if datetime.datetime.fromisoformat(row['start_time']).date() == today
    ]
    for record in today_records:
        idx = next(
            (i for i, p in enumerate(projects) if p['project'] == record['project']), None)
        start_time = record['start_time']
        end_time = record['end_time']
        if end_time is None:
            end_time = datetime.datetime.now().isoformat()
            projects[idx]['timer_running'] = True
        duration = datetime.datetime.fromisoformat(
            end_time) - datetime.datetime.fromisoformat(start_time)
        if 'duration' in projects[idx]:
            projects[idx]['duration'] = projects[idx]['duration'] + duration
        else:
            projects[idx]['duration'] = duration

    # display
    print("\n")
    for idx, proj in enumerate(projects, 1):
        duration = proj.get('duration', datetime.timedelta())
        hours_decimal = duration.total_seconds() / 3600
        running = ""
        if proj['timer_running']:
            running = "*"
        print(f"{idx}. {proj['project']} - {hours_decimal:.2f}{running} hrs")


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
    show_project_list()
    show_default_options()
    process_user_input()


if __name__ == "__main__":
    main()
    exit()
