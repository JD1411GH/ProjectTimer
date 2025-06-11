import sys
import dataset
import datetime
import os
import threading
import time

# database connection
db = dataset.connect('sqlite:///project-timer.db')
table = db["time_records"]

# globals
display_entries = {}


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def daily_report():
    pass


def exit():
    global db
    db.executable.close()
    sys.exit(0)


def process_user_input():
    choice = input("")
    if choice == "p":
        plan_task()
    elif choice == "s":
        stop_timer()
    elif choice == "d":
        daily_report()
    elif choice == "x":
        exit()
    elif int(choice) > 0 and int(choice) <= len(display_entries):
        key = list(display_entries.keys())[int(choice) - 1]
        print(key)
        # show_tasks(int(choice))
        exit()
    else:
        print("Invalid choice. Please try again.")
        process_user_input()


def refresh():
    os.system('cls' if os.name == 'nt' else 'clear')
    show_project_status()
    show_default_options()


def show_default_options():
    print("\n[s] Stop timer")
    print("[p] Plan task")
    print("[d] Day summary")
    print("[t] Task summary")
    print("[x] Exit")
    print("\nEnter your choice: ", end="")


def show_project_status():
    global table
    global display_entries

    # add today's tasks
    today = datetime.date.today().isoformat()
    rows = list(table.find(start_time={'like': f"{today}%"}))

    # populate display_entries
    display_entries.clear()
    for row in rows:
        key = f"[{row['project']}] {row['task']}"
        if key in display_entries:
            start = datetime.datetime.fromisoformat(row['start_time'])
            end = datetime.datetime.fromisoformat(
                row['end_time']) if row['end_time'] else datetime.datetime.now()
            duration = (end - start).total_seconds() / 3600  # hours in decimal
            display_entries[key] = {
                'actual_effort': round(duration, 2) + display_entries[key]['actual_effort'],
                'planned_effort': row['planned_effort'] if 'planned_effort' in row else 0,
                'running': "" if row['end_time'] else "*"
            }
        else:
            start = datetime.datetime.fromisoformat(row['start_time'])
            end = datetime.datetime.fromisoformat(
                row['end_time']) if row['end_time'] else datetime.datetime.now()
            duration = (end - start).total_seconds() / 3600  # hours in decimal
            display_entries[key] = {
                'actual_effort': round(duration, 2),
                'planned_effort': 0 if row['planned_effort'] is None else row['planned_effort'],
                'running': "" if row['end_time'] else "*"
            }

    # show display_entries
    for idx, (key, entry) in enumerate(display_entries.items(), 1):
        print(
            f"{idx}. {key} - {entry['actual_effort']}{entry['running']} / {entry['planned_effort']} hrs")


def show_tasks(project_id):
    os.system('cls' if os.name == 'nt' else 'clear')

    project_name = display_entries[project_id - 1]['project']
    tasks = list({row['task'] for row in table.find(project=project_name)})
    if not tasks:
        print(f"No tasks found for project '{project_name}'.")
    else:
        print(f"Tasks for project '{project_name}':")
        for idx, task in enumerate(tasks, 1):
            print(f"{idx}. {task}")

    task_id = int(input("\n Select task to start: "))
    if task_id > 0 and task_id <= len(tasks):
        start_timer(display_entries[project_id - 1]
                    ['project'], tasks[task_id - 1])
    else:
        print("Invalid input")
        show_tasks(project_id)


def start_timer(project, task):
    global table
    table.insert({
        "project": project,
        "task": task,
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": None,
    })
    refresh()


def stop_timer():
    global table

    running_records = list(table.find(end_time=None))
    if not running_records:
        return
    for record in running_records:
        table.update(
            dict(id=record['id'],
                 end_time=datetime.datetime.now().isoformat()),
            ['id']
        )


def periodic_refresh():
    while True:
        time.sleep(300)  # 5 minutes
        try:
            refresh()
        except Exception as e:
            print(f"Error during periodic refresh: {e}")


def plan_task():
    global table

    clear()

    # select project
    projects = set(row['project'] for row in table.all())
    for idx, project in enumerate(projects, 1):
        print(f"{idx}. {project}")
    print("0. New project")
    project_idx = input("\nSelect project: ")

    if project_idx == "0":
        project = input("Enter project name: ")
    else:
        project_list = list(projects)
        project = project_list[int(project_idx) - 1]

    # select task
    tasks = set(row['task'] for row in table.find(project=project))
    for idx, task in enumerate(tasks, 1):
        print(f"{idx}. {task}")
    print("0. New task")
    task_idx = input("\nSelect task: ")

    if task_idx == "0":
        task = input("Enter task name: ")
    else:
        task_list = list(tasks)
        task = task_list[int(task_idx) - 1]

    planned_effort = input("Planned effort: ")

    table.insert({
        "project": project,
        "task": task,
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": datetime.datetime.now().isoformat(),
        "planned_effort": int(planned_effort)
    })
    refresh()


def main():
    # Start background thread for periodic refresh
    t = threading.Thread(target=periodic_refresh, daemon=True)
    t.start()
    while True:
        refresh()
        process_user_input()


if __name__ == "__main__":
    main()
    exit()
