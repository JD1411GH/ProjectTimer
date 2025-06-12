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
active_action = False


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def day_summary():
    global active_action
    active_action = True

    day = datetime.date.today()

    while True:
        clear()
        rows = list(table.find(start_time={'like': f"{day.isoformat()}%"}))
        if not rows:
            print(f"No records found for {day.isoformat()}.")
        else:
            projects = {}
            for row in rows:
                start = datetime.datetime.fromisoformat(row['start_time'])
                end = datetime.datetime.fromisoformat(
                    row['end_time']) if row['end_time'] else datetime.datetime.now()
                # effort in hours, rounded to 2 decimals
                effort = round((end - start).total_seconds() / 3600, 2)
                if row['project'] in projects:
                    projects[row['project']] += effort
                else:
                    projects[row['project']] = effort
            for project, effort in projects.items():
                print(f"{project}: {effort} hrs")

        choice = input(
            "\n[p] previous day  [n] next day  [q] quit: ").strip().lower()
        if choice == "p":
            day -= datetime.timedelta(days=1)
        elif choice == "n":
            day += datetime.timedelta(days=1)
        elif choice == "q":
            break
        else:
            print("Invalid choice.")

    active_action = False


def exit():
    global db
    db.executable.close()
    sys.exit(0)


def process_user_input():
    global active_action
    active_action = True

    choice = input("")
    if choice == "p":
        plan_task()
    elif choice == "s":
        stop_timer()
    elif choice == "d":
        day_summary()
    elif choice == "x":
        exit()
    elif int(choice) > 0 and int(choice) <= len(display_entries):
        key = list(display_entries.keys())[int(choice) - 1]
        project = key.split("]")[0][1:]
        task = key.split("]")[1][1:]
        start_timer(project, task)
    else:
        print("Invalid choice. Please try again.")
        process_user_input()
    active_action = False


def refresh():
    os.system('cls' if os.name == 'nt' else 'clear')
    show_project_status()
    show_default_options()


def show_default_options():
    options = [
        ("[s]", "Stop timer", ""),
        ("[p]", "Plan task", ""),
        ("[d]", "Day summary", ""),
        ("[t]", "Task summary", ""),
        ("[x]", "Exit", "")
    ]

    col_width = 20
    num_cols = 3

    # Pad options to fill the last row
    padded_options = options + \
        [("", "", "")] * ((num_cols - len(options) % num_cols) % num_cols)

    print()
    for i in range(0, len(padded_options), num_cols):
        row = padded_options[i:i+num_cols]
        line = ""
        for opt in row:
            text = f"{opt[0]} {opt[1]}".ljust(col_width)
            line += text
        print(line)
    print("\nEnter your choice: ", end="")


def show_project_status():
    global table
    global display_entries

    # add today's tasks
    today = datetime.date.today().isoformat()
    rows = list(table.find(start_time={'like': f"{today}%"}))
    if len(rows) == 0:
        print("No tasks found for today.")
        return

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
    total_planned_effort = 0
    total_actual_effort = 0
    for idx, (key, entry) in enumerate(display_entries.items(), 1):
        total_planned_effort += 0 if entry['planned_effort'] is None else entry['planned_effort']
        total_actual_effort += 0 if entry['actual_effort'] is None else entry['actual_effort']
        print(
            f"{idx}. {key} - {entry['actual_effort']}{entry['running']} / {entry['planned_effort']} hrs")
    print(
        f"\nTotal effort: {total_actual_effort} / {total_planned_effort} hrs")


def start_timer(project, task):
    global table

    stop_timer()

    # find planned effort
    planned_effort = 0
    planned_effort_row = table.find_one(project=project, task=task)
    if planned_effort_row and 'planned_effort' in planned_effort_row:
        planned_effort = planned_effort_row['planned_effort']

    # insert into database
    table.insert({
        "project": project,
        "task": task,
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": None,
        "planned_effort": planned_effort
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
            if not active_action:
                refresh()
        except Exception as e:
            print(f"Error during periodic refresh: {e}")


def plan_task():
    global table
    global active_action

    active_action = True
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
        "planned_effort": float(planned_effort)
    })

    active_action = False
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
