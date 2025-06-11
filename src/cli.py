import sys
import dataset
import datetime
import os

# database connection
db = dataset.connect('sqlite:///project-timer.db')
table = db["time_records"]

# globals
projects = []


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
    elif int(choice) > 0 and int(choice) <= len(projects):
        show_tasks(int(choice))
    else:
        print("Invalid choice. Please try again.")
        process_user_input()


def refresh():
    os.system('cls' if os.name == 'nt' else 'clear')
    show_projects_status()
    show_default_options()
    process_user_input()


def show_default_options():
    print("0. New task")
    print("\n[s] Stop timer")
    print("[x] Exit")


def show_projects_status():
    global table
    global projects

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
        if 'duration' in proj:
            duration = proj.get('duration', datetime.timedelta())
        else:
            duration = 0
        hours_decimal = duration.total_seconds() / 3600
        running = ""
        if 'timer_running' in proj and proj['timer_running']:
            running = "*"
        print(f"{idx}. {proj['project']} - {hours_decimal:.2f}{running} hrs")


def show_tasks(project_id):
    os.system('cls' if os.name == 'nt' else 'clear')

    project_name = projects[project_id - 1]['project']
    tasks = list({row['task'] for row in table.find(project=project_name)})
    if not tasks:
        print(f"No tasks found for project '{project_name}'.")
    else:
        print(f"Tasks for project '{project_name}':")
        for idx, task in enumerate(tasks, 1):
            print(f"{idx}. {task}")

    task_id = int(input("\n Select task to start: "))
    if task_id > 0 and task_id <= len(tasks):
        start_timer(projects[project_id - 1]['project'], tasks[task_id - 1])
    else:
        print("Invalid input")
        show_tasks(project_id)


def start_timer(project, task):
    global table
    table.insert({
        "project": project,
        "task": task,
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": None
    })
    refresh()


def stop_timer():
    running_records = list(table.find(end_time=None))
    if not running_records:
        return
    for record in running_records:
        table.update(
            dict(id=record['id'],
                 end_time=datetime.datetime.now().isoformat()),
            ['id']
        )


def main():
    while True:
        refresh()


if __name__ == "__main__":
    main()
    exit()
