import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import csv
import os
import subprocess

SCHEDULE_CSV = "schedules.csv"

def update_system_schedule(schedule_info):
    task_name = schedule_info["Schedule Name"]
    enabled = schedule_info["Enabled"].lower() == "yes"
    start_dt = schedule_info["Start DateTime"]
    try:
        start_time = start_dt.split()[-1]
    except Exception:
        start_time = "10:00"
    freq_map = {"Once": "ONCE", "Once in Day": "DAILY", "Hourly": "HOURLY"}
    frequency = freq_map.get(schedule_info["Frequency"], "ONCE")
    program_path = schedule_info["Program Path"]
    selected_tasks = schedule_info["Selected Tasks"]
    task_cmd = f'python "{program_path}" "{selected_tasks}"'

    if enabled:
        cmd = [
            "schtasks",
            "/Create",
            "/SC", frequency,
            "/TN", task_name,
            "/TR", task_cmd,
            "/ST", start_time,
            "/F"
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"Created system schedule for '{task_name}'")
        except Exception as e:
            messagebox.showerror("System Task Error", f"Error creating schedule:\n{e}")
    else:
        cmd = ["schtasks", "/Delete", "/TN", task_name, "/F"]
        try:
            subprocess.run(cmd, check=True)
            print(f"Deleted system schedule for '{task_name}'")
        except Exception as e:
            print(f"Delete may fail if not created previously: {e}")

class TaskScheduleForm(tk.Toplevel):
    def __init__(self, master, tasks):
        super().__init__(master)
        self.title("Task Schedule")
        self.geometry("600x340")
        self.tasks = tasks

        self.schedule_name = tk.StringVar()
        self.enabled = tk.StringVar(value="Yes")
        self.start_datetime = tk.StringVar(value=datetime.now().strftime("%m/%d/%Y %H:%M"))
        self.frequency = tk.StringVar(value="Once")
        self.program_path = tk.StringVar(value="C:\\Bakp.py")
        self.selected_tasks = []

        # Form fields (left)
        left = tk.Frame(self)
        left.pack(side=tk.LEFT, padx=10, pady=12, fill=tk.Y)

        tk.Label(left, text="Schedule Name").grid(row=0, column=0, sticky='w')
        tk.Entry(left, textvariable=self.schedule_name, width=25).grid(row=0, column=1, sticky='w')

        tk.Label(left, text="Enabled (Yes/No)").grid(row=1, column=0, sticky='w')
        ttk.Combobox(left, textvariable=self.enabled, values=["Yes", "No"], state="readonly", width=10).grid(row=1, column=1, sticky='w')

        tk.Label(left, text="Start DateTime").grid(row=2, column=0, sticky='w')
        tk.Entry(left, textvariable=self.start_datetime, width=25).grid(row=2, column=1, sticky='w')

        tk.Label(left, text="Frequency").grid(row=3, column=0, sticky='w')
        ttk.Combobox(left, textvariable=self.frequency, values=["Once", "Once in Day", "Hourly"], state="readonly", width=20).grid(row=3, column=1, sticky='w')

        tk.Label(left, text="Select Tasks").grid(row=4, column=0, sticky='nw')
        self.tasks_listbox = tk.Listbox(left, selectmode=tk.MULTIPLE, width=25, height=6)
        self.tasks_listbox.grid(row=4, column=1, sticky='w', pady=2)
        for t in self.tasks:
            self.tasks_listbox.insert(tk.END, t)

        tk.Label(left, text="Program Name").grid(row=5, column=0, sticky='w')
        tk.Entry(left, textvariable=self.program_path, width=25).grid(row=5, column=1, sticky='w')

        btn_frame = tk.Frame(left)
        btn_frame.grid(row=6, column=1, sticky='ew', pady=12)
        tk.Button(btn_frame, text="Save Schedule", command=self.save_schedule, width=12).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Reset", command=self.reset_fields, width=12).pack(side=tk.LEFT, padx=2)

        # Listbox (right): Schedule names
        right = tk.Frame(self, bg="#fbf3f3", width=180)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=7)
        tk.Label(right, text="List to Schedule", fg="red", bg="#fbf3f3").pack(pady=(10,0))
        self.schedule_listbox = tk.Listbox(right, width=24, height=14)
        self.schedule_listbox.pack(pady=10, padx=10, fill=tk.Y)
        self.schedule_listbox.bind("<<ListboxSelect>>", self.load_selected_schedule)

        self.load_schedules_listbox()

    def save_schedule(self):
        selected = [self.tasks[i] for i in self.tasks_listbox.curselection()]
        selected_str = ",".join(selected)
        data = {
            "Schedule Name": self.schedule_name.get(),
            "Enabled": self.enabled.get(),
            "Start DateTime": self.start_datetime.get(),
            "Frequency": self.frequency.get(),
            "Selected Tasks": selected_str,
            "Program Path": self.program_path.get()
        }

        schedules = []
        updated = False
        if os.path.exists(SCHEDULE_CSV):
            with open(SCHEDULE_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Schedule Name"] == data["Schedule Name"]:
                        schedules.append(data)
                        updated = True
                    else:
                        schedules.append(row)
        if not updated:
            schedules.append(data)

        with open(SCHEDULE_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            writer.writeheader()
            writer.writerows(schedules)

        update_system_schedule(data)

        messagebox.showinfo("Saved", f"Schedule '{data['Schedule Name']}' saved!")
        self.load_schedules_listbox()

    def reset_fields(self):
        self.schedule_name.set("")
        self.enabled.set("Yes")
        self.start_datetime.set(datetime.now().strftime("%m/%d/%Y %H:%M"))
        self.frequency.set("Once")
        self.program_path.set("C:\\Bakp.py")
        self.tasks_listbox.selection_clear(0, tk.END)

    def load_schedules_listbox(self):
        self.schedule_listbox.delete(0, tk.END)
        self.all_schedules = []
        if os.path.exists(SCHEDULE_CSV):
            with open(SCHEDULE_CSV, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.all_schedules = list(reader)
            for sched in self.all_schedules:
                self.schedule_listbox.insert(tk.END, sched["Schedule Name"])

    def load_selected_schedule(self, event):
        sel = self.schedule_listbox.curselection()
        if not sel:
            return
        index = sel[0]
        data = self.all_schedules[index]
        self.schedule_name.set(data["Schedule Name"])
        self.enabled.set(data["Enabled"])
        self.start_datetime.set(data["Start DateTime"])
        self.frequency.set(data["Frequency"])
        self.program_path.set(data["Program Path"])
        self.tasks_listbox.selection_clear(0, tk.END)
        selected_tasks = data.get("Selected Tasks", "").split(",")
        for i, t in enumerate(self.tasks):
            if t in selected_tasks:
                self.tasks_listbox.select_set(i)

if __name__ == "__main__":
    task_names = ["Task 10", "Task 6", "Task 7", "Task 9", "Test 8"]
    root = tk.Tk()
    root.title("Task Schedule")
    TaskScheduleForm(root, task_names)
    root.mainloop()

