import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import getpass
import csv
import os
import subprocess

SCHEDULE_CSV = "schedules.csv"


TASK_XML_TEMPLATE = '''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{dt}</Date>
    <Author>FPS\\{author}</Author>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>{start_dt}</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>    
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT72H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>"{script_path}" "{tasks}"</Arguments>
      <WorkingDirectory>{start_in}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
'''

def xml_escape(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&apos;"))


def create_task_xml(task_name, python_path, script_path, start_in, start_dt, tasks):
    xml = TASK_XML_TEMPLATE.format(
        dt=datetime.now().isoformat(),
        author=getpass.getuser(),
        start_dt=start_dt,  # ISO format "2025-11-01T18:00:00"
        python_path=xml_escape(python_path),
        script_path=xml_escape(script_path),
        tasks=xml_escape(tasks),
        start_in=xml_escape(start_in)
    )
    filename = f"{task_name}_schedule.xml"
    with open(filename, "w", encoding="utf-16") as f:
        f.write(xml)
    return filename

def update_system_schedule(schedule_info):
    task_name = schedule_info["Schedule Name"]
    enabled = schedule_info["Enabled"].lower() == "yes"
    python_path = os.path.normpath(schedule_info["Python Path"])
    script_path = os.path.normpath(schedule_info["Script Path"])
    start_in = os.path.normpath(schedule_info["Start In"])
    selected_tasks = schedule_info["Selected Tasks"]
    try:
        start_dt = datetime.strptime(schedule_info["Start DateTime"], "%m/%d/%Y %H:%M").strftime("%Y-%m-%dT%H:%M:00")
    except Exception:
        start_dt = datetime.now().strftime("%Y-%m-%dT%H:%M:00")
    if enabled:
        xml_file = create_task_xml(task_name, python_path, script_path, start_in, start_dt, selected_tasks)
        cmd = ["schtasks", "/Create", "/TN", task_name, "/XML", xml_file, "/F"]
        try:
            subprocess.run(cmd, check=True)
            print(f"Created system schedule for '{task_name}' (Start in set)")
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
        self.geometry("800x380")
        self.tasks = tasks
        self.schedule_name = tk.StringVar()
        self.enabled = tk.StringVar(value="Yes")
        self.start_datetime = tk.StringVar(value=datetime.now().strftime("%m/%d/%Y %H:%M"))
        self.frequency = tk.StringVar(value="Once")
        self.python_path = tk.StringVar(value=r"C:\Users\manojkumar.pilane\AppData\Local\Programs\Python\Python310\python.exe")
        self.script_path = tk.StringVar(value=r"C:\Bakp.py")
        self.start_in = tk.StringVar(value=r"C:\Users\manojkumar.pilane\Documents\Python\GIT\UtilityPrograms\BackupTask")
        self.selected_tasks = []
        self.all_schedules = []

        left = tk.Frame(self)
        left.pack(side=tk.LEFT, padx=10, pady=12, fill=tk.Y)

        tk.Label(left, text="Schedule Name").grid(row=0, column=0, sticky='w')
        tk.Entry(left, textvariable=self.schedule_name, width=28).grid(row=0, column=1, sticky='w')

        tk.Label(left, text="Enabled (Yes/No)").grid(row=1, column=0, sticky='w')
        ttk.Combobox(left, textvariable=self.enabled, values=["Yes", "No"], state="readonly", width=12).grid(row=1, column=1, sticky='w')

        tk.Label(left, text="Start DateTime").grid(row=2, column=0, sticky='w')
        tk.Entry(left, textvariable=self.start_datetime, width=28).grid(row=2, column=1, sticky='w')

        tk.Label(left, text="Frequency").grid(row=3, column=0, sticky='w')
        ttk.Combobox(left, textvariable=self.frequency, values=["Once", "Once in Day", "Hourly"], state="readonly", width=20).grid(row=3, column=1, sticky='w')

        tk.Label(left, text='Program/script (Python Path)').grid(row=4, column=0, sticky='w')
        python_entry = tk.Entry(left, textvariable=self.python_path, width=37)
        python_entry.grid(row=4, column=1, sticky='w')
        tk.Button(left, text="Browse", command=self.browse_python).grid(row=4, column=2, sticky='w')

        tk.Label(left, text='Add arguments (Bakp.py)').grid(row=5, column=0, sticky='w')
        script_entry = tk.Entry(left, textvariable=self.script_path, width=37)
        script_entry.grid(row=5, column=1, sticky='w')
        tk.Button(left, text="Browse", command=self.browse_script).grid(row=5, column=2, sticky='w')

        tk.Label(left, text='Start In (Working directory)').grid(row=6, column=0, sticky='w')
        startin_entry = tk.Entry(left, textvariable=self.start_in, width=37)
        startin_entry.grid(row=6, column=1, sticky='w')
        tk.Button(left, text="Browse", command=self.browse_startin).grid(row=6, column=2, sticky='w')

        tk.Label(left, text="Select Tasks").grid(row=7, column=0, sticky='nw')
        self.tasks_listbox = tk.Listbox(left, selectmode=tk.MULTIPLE, width=28, height=6)
        self.tasks_listbox.grid(row=7, column=1, sticky='w', pady=4)
        for t in self.tasks:
            self.tasks_listbox.insert(tk.END, t)

        btn_frame = tk.Frame(left)
        btn_frame.grid(row=8, column=1, sticky='ew', pady=12)
        tk.Button(btn_frame, text="Save Schedule", command=self.save_schedule, width=15).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Reset", command=self.reset_fields, width=15).pack(side=tk.LEFT, padx=4)

        right = tk.Frame(self, bg="#fbf3f3", width=200)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=7)
        tk.Label(right, text="List to Schedule", fg="red", bg="#fbf3f3").pack(pady=(10,0))
        self.schedule_listbox = tk.Listbox(right, width=26, height=14)
        self.schedule_listbox.pack(pady=10, padx=10, fill=tk.Y)
        self.schedule_listbox.bind("<<ListboxSelect>>", self.load_selected_schedule)

        self.load_schedules_listbox()

    def browse_python(self):
        path = filedialog.askopenfilename(title="Select Python Executable",
                                          filetypes=[("Python Executable", "python*.exe"), ("All Files", "*.*")])
        if path:
            self.python_path.set(path)

    def browse_script(self):
        path = filedialog.askopenfilename(title="Select Bakp.py Script",
                                          filetypes=[("Python Script", "*.py"), ("All Files", "*.*")])
        if path:
            self.script_path.set(path)

    def browse_startin(self):
        path = filedialog.askdirectory(title="Select Start In Working Directory")
        if path:
            self.start_in.set(path)

    def save_schedule(self):
        selected = [self.tasks[i] for i in self.tasks_listbox.curselection()]
        selected_str = ",".join(selected)
        data = {
            "Schedule Name": self.schedule_name.get(),
            "Enabled": self.enabled.get(),
            "Start DateTime": self.start_datetime.get(),
            "Frequency": self.frequency.get(),
            "Python Path": self.python_path.get(),
            "Script Path": self.script_path.get(),
            "Start In": self.start_in.get(),
            "Selected Tasks": selected_str,
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
        self.python_path.set(r"C:\Users\manojkumar.pilane\AppData\Local\Programs\Python\Python310\python.exe")
        self.script_path.set(r"C:\Bakp.py")
        self.start_in.set(r"C:\Users\manojkumar.pilane\Documents\Python\GIT\UtilityPrograms\BackupTask")
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
        self.python_path.set(data.get("Python Path", r"C:\Users\manojkumar.pilane\AppData\Local\Programs\Python\Python310\python.exe"))
        self.script_path.set(data.get("Script Path", r"C:\Bakp.py"))
        self.start_in.set(data.get("Start In", r"C:\Users\manojkumar.pilane\Documents\Python\GIT\UtilityPrograms\BackupTask"))
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
