from datetime import datetime
from pathlib import Path
import json
import random
import secrets
import string
import subprocess
import sys
import time


FOLDER = Path(__file__).resolve().parent
TODO_FILE = FOLDER / "todo.json"
NOTES_FILE = FOLDER / "notes.txt"


def calculator():
    print("Calculator — enter an expression, or type back to return.")

    while True:
        expression = input("calc> ").strip()

        if expression.lower() == "back":
            return

        allowed = set("0123456789+-*/(). %")
        if not expression or any(char not in allowed for char in expression):
            print("Enter a simple arithmetic expression.")
            continue

        try:
            print(eval(expression, {"__builtins__": {}}, {}))
        except (SyntaxError, ZeroDivisionError):
            print("That expression didn't work.")


def timer():
    try:
        seconds = int(input("How many seconds? "))
        if seconds < 1:
            print("Enter a number greater than zero.")
            return

        print("Timer started.")
        time.sleep(seconds)
        print("Time's up!")
    except ValueError:
        print("Please enter a whole number.")
    except KeyboardInterrupt:
        print("\nTimer stopped.")


def convert():
    print("Temperature conversion: C to F, or F to C.")
    direction = input("Which conversion? ").strip().lower()

    try:
        value = float(input("Temperature: "))

        if direction == "c to f":
            print(f"{value}°C = {(value * 9 / 5) + 32:.2f}°F")
        elif direction == "f to c":
            print(f"{value}°F = {(value - 32) * 5 / 9:.2f}°C")
        else:
            print("Type 'C to F' or 'F to C'.")
    except ValueError:
        print("Please enter a number.")


def notes():
    print(f"Notes are saved in {NOTES_FILE.name}.")
    note = input("Write a note: ").strip()

    if note:
        with NOTES_FILE.open("a", encoding="utf-8") as file:
            file.write(note + "\n")
        print("Note saved.")
    else:
        print("Nothing to save.")


def generate_password():
    try:
        length = int(input("Password length (4–128): "))
        if not 4 <= length <= 128:
            print("Choose a length from 4 to 128.")
            return

        characters = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
        password = "".join(
            secrets.choice(characters) for _ in range(length)
        )
        print(password)
    except ValueError:
        print("Please enter a whole number.")


def roll_dice():
    try:
        count = int(input("How many dice? "))
        sides = int(input("How many sides per die? "))

        if count < 1 or sides < 2:
            print("Use at least 1 die and at least 2 sides.")
            return

        rolls = [random.randint(1, sides) for _ in range(count)]
        print(f"Rolls: {rolls}  Total: {sum(rolls)}")
    except ValueError:
        print("Please enter whole numbers.")


def flip_coin():
    print(random.choice(["Heads", "Tails"]))


def load_todos():
    try:
        with TODO_FILE.open("r", encoding="utf-8") as file:
            tasks = json.load(file)

        for task in tasks:
            task.setdefault("done", False)

        return tasks
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError):
        print("Couldn't read todo.json.")
        return []


def todo():
    tasks = load_todos()

    def save_tasks():
        TODO_FILE.write_text(
            json.dumps(tasks, indent=2),
            encoding="utf-8"
        )

    while True:
        print("\nTodo: [a]dd, [v]iew, [d]one, [r]emove completed, [b]ack")
        choice = input("> ").strip().lower()

        if choice == "a":
            task_text = input("Task: ").strip()
            if task_text:
                tasks.append({"task": task_text, "done": False})
                save_tasks()
                print("Task added.")

        elif choice == "v":
            if not tasks:
                print("No tasks yet.")
            else:
                for number, task in enumerate(tasks, start=1):
                    mark = "✓" if task.get("done", False) else " "
                    print(f"{number}. [{mark}] {task['task']}")

        elif choice == "d":
            try:
                number = int(input("Task number to mark done: "))
                if 1 <= number <= len(tasks):
                    tasks[number - 1]["done"] = True
                    save_tasks()
                    print("Marked as done and saved.")
                else:
                    print("No task with that number.")
            except ValueError:
                print("Please enter a task number.")

        elif choice == "r":
            completed = [
                task for task in tasks
                if task.get("done", False)
            ]

            if not completed:
                print("There are no completed tasks to remove.")
                continue

            print("Completed tasks:")
            for number, task in enumerate(completed, start=1):
                print(f"{number}. {task['task']}")

            try:
                number = int(
                    input("Number from this completed-task list to remove: ")
                )

                if 1 <= number <= len(completed):
                    task_to_remove = completed[number - 1]
                    tasks.remove(task_to_remove)
                    save_tasks()
                    print("Removed.")
                else:
                    print("Choose a number from the completed-task list.")
            except ValueError:
                print("Please enter a task number.")

        elif choice == "b":
            return

        else:
            print("Choose a, v, d, r, or b.")


def random_picker():
    print("Type 'number' for a random number or 'choice' to pick from options.")
    mode = input("> ").strip().lower()

    if mode == "number":
        try:
            low = int(input("From: "))
            high = int(input("To: "))
            print(random.randint(low, high))
        except ValueError:
            print("Enter whole numbers, with the smaller number first.")
    elif mode == "choice":
        options = input("Enter choices separated by commas: ").split(",")
        options = [option.strip() for option in options if option.strip()]

        if options:
            print(random.choice(options))
        else:
            print("You didn't enter any choices.")
    else:
        print("Type 'number' or 'choice'.")


def show_date():
    print(datetime.now().strftime("%A, %B %d, %Y — %I:%M:%S %p"))


def text_edit():
    editor = FOLDER / "txteditor.py"

    if not editor.is_file():
        print("Couldn't find txteditor.py beside toolbox.py.")
        return

    subprocess.run([sys.executable, str(editor)])


def show_help():
    print("""
Commands:
  calc       Calculator
  timer      Countdown timer
  convert    Convert Celsius and Fahrenheit
  notes      Save a note
  password   Generate a random password
  dice       Roll dice
  coin       Flip a coin
  todo       Add, view, complete, or remove tasks
  random     Pick a number or choose from a list
  date       Show the date and time
  textedit   Launch txteditor.py
  help       Show this command list
  quit       Exit
""")


def main():
    print("Welcome to your toolbox! Type 'help' to see commands.")

    commands = {
        "calc": calculator,
        "timer": timer,
        "convert": convert,
        "notes": notes,
        "password": generate_password,
        "dice": roll_dice,
        "coin": flip_coin,
        "todo": todo,
        "random": random_picker,
        "date": show_date,
        "textedit": text_edit,
        "help": show_help,
    }

    while True:
        command = input("> ").strip().lower()

        if command in ("quit", "exit"):
            print("Bye!")
            break
        elif command in commands:
            commands[command]()
        elif command:
            print(f"Unknown command: {command}. Type 'help'.")


if __name__ == "__main__":
    main()
