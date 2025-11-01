import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import csv
import os

from TaskScheduleForm import TaskScheduleForm


GRID_CSV = "paths.csv"

class FileCopyMasterPage:
    def __init__(self, root):
        self.root = root
        self.root.title("File Copy Scheduler Master Page")

        self.task_name = tk.StringVar()
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.backup_type = tk.StringVar(value="Normal")  # New field; default to Normal
        self.editing_index = None

        action_btn_frame = tk.Frame(root)
        action_btn_frame.grid(row=4, column=1, columnspan=4, sticky='w', padx=2, pady=2)

        # Task Name Entry
        tk.Label(root, text="Task Name").grid(row=0, column=0, sticky='w')
        tk.Entry(root, textvariable=self.task_name, width=30).grid(row=0, column=1, columnspan=2, sticky='w', padx=2, pady=2)

        # Source Path Entry and Browse
        tk.Label(root, text="Source Path").grid(row=1, column=0, sticky='w')
        tk.Entry(root, textvariable=self.source_path, width=30).grid(row=1, column=1, sticky='w', padx=2, pady=2)
        tk.Button(root, text="Browse Source", command=self.browse_source).grid(row=1, column=2, sticky='ew', padx=2, pady=2)

        # Destination Path Entry and Browse
        tk.Label(root, text="Dist Path").grid(row=2, column=0, sticky='w')
        tk.Entry(root, textvariable=self.dest_path, width=30).grid(row=2, column=1, sticky='w', padx=2, pady=2)
        tk.Button(root, text="Browse Destination", command=self.browse_dest).grid(row=2, column=2, sticky='ew', padx=2, pady=2)

        # Backup Type dropdown
        tk.Label(root, text="Backup Type").grid(row=3, column=0, sticky='w')
        backup_type_combo = ttk.Combobox(root, textvariable=self.backup_type, values=["Normal", "Zip"], state="readonly", width=28)
        backup_type_combo.grid(row=3, column=1, sticky='w', padx=2, pady=2)

        # Buttons

        add_btn = tk.Button(action_btn_frame, text="Add to Grid", command=self.add_to_grid, width=11)
        add_btn.pack(side=tk.LEFT, padx=(0, 6))

        create_btn = tk.Button(action_btn_frame, text="Create Task", command=self.schedule_task, width=11)
        create_btn.pack(side=tk.LEFT, padx=(0, 6))

        reset_btn = tk.Button(action_btn_frame, text="Reset", command=self.grid_reset, width=7)
        reset_btn.pack(side=tk.LEFT, padx=(0, 6))

        delete_btn = tk.Button(action_btn_frame, text="Delete Selected", command=self.remove_selected_task, width=13)
        delete_btn.pack(side=tk.LEFT, padx=(0, 6))

        open_sched_btn = tk.Button(action_btn_frame, text="Open Scheduler", command=self.open_scheduler, width=13)
        open_sched_btn.pack(side=tk.LEFT)


        # Treeview
        columns = ('#', 'Select', 'Task Name', 'Source Path', 'Destination Path', 'Backup Type', 'Action')
        self.tree = ttk.Treeview(root, columns=columns, show='headings', height=8)
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column('#', width=30, anchor='center')
        self.tree.column('Select', width=60, anchor='center')
        self.tree.column('Task Name', width=120, anchor='w')
        self.tree.column('Source Path', width=180, anchor='w')
        self.tree.column('Destination Path', width=180, anchor='w')
        self.tree.column('Backup Type', width=80, anchor='center')
        self.tree.column('Action', width=80, anchor='center')
        self.tree.grid(row=6, column=0, columnspan=5, padx=5, pady=10)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.handle_action)

        self.entries = []
        self.load_grid_from_csv()

        # Task list
        tk.Label(root, text="List of Task").grid(row=0, column=5, padx=10, sticky='nw')
        self.task_list = tk.Listbox(root, height=20, width=25)
        self.task_list.grid(row=1, column=5, rowspan=6, padx=10, sticky='n')
        self.task_list.bind('<<ListboxSelect>>', self.on_task_select)
        self.load_task_list_from_csv()

    def browse_source(self):
        path = filedialog.askdirectory(title="Select Source Directory")
        if path:
            self.source_path.set(path)

    def browse_dest(self):
        path = filedialog.askdirectory(title="Select Destination Directory")
        if path:
            self.dest_path.set(path)

    def add_to_grid(self):
        task = self.task_name.get().strip()
        src = self.source_path.get().strip()
        dst = self.dest_path.get().strip()
        backup_type = self.backup_type.get()
        if not task or not src or not dst:
            messagebox.showerror("Error", "Task name, source and destination path must not be empty!")
            return
        if self.editing_index is not None:
            selected = self.entries[self.editing_index][4]
            self.entries[self.editing_index] = (task, src, dst, backup_type, selected)
            self.editing_index = None
        else:
            self.entries.append((task, src, dst, backup_type, False))
        self.refresh_tree()
        self.reset_fields()

    def refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, (task, src, dst, backup_type, selected) in enumerate(self.entries, start=1):
            sel_text = "[X]" if selected else "[ ]"
            self.tree.insert('', 'end', values=(idx, sel_text, task, src, dst, backup_type, "Edit/Delete"))

    def on_tree_click(self, event):
        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row_id:
            return
        if col == "#2":  # Select column clicked
            item = self.tree.item(row_id)
            values = list(item['values'])
            index = int(values[0]) - 1
            selected = self.entries[index][4]
            self.entries[index] = (self.entries[index][0], self.entries[index][1], self.entries[index][2], self.entries[index][3], not selected)
            self.refresh_tree()

    def handle_action(self, event):
        row_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not row_id or col != "#7":  # Only edit/delete on Action column
            return
        item = self.tree.item(row_id)
        index = int(item['values'][0]) - 1
        result = messagebox.askquestion("Select Action", "Edit (Yes) or Delete (No)?", icon='question', type='yesno')
        if result == "yes":
            task, src, dst, backup_type, selected = self.entries[index]
            self.task_name.set(task)
            self.source_path.set(src)
            self.dest_path.set(dst)
            self.backup_type.set(backup_type)
            self.editing_index = index
        elif result == "no":
            del self.entries[index]
            self.refresh_tree()

    def reset_fields(self):
        self.task_name.set("")
        self.source_path.set("")
        self.dest_path.set("")
        self.backup_type.set("Normal")
        self.editing_index = None

    def grid_reset(self):
        self.entries.clear()
        self.refresh_tree()
        self.reset_fields()

    def schedule_task(self):
        # Read all rows except the currently-edited task group
        current_task = self.task_name.get().strip()
        new_entries = self.entries.copy()
        other_entries = []
        if os.path.exists(GRID_CSV):
            with open(GRID_CSV, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    backup_type = row.get("BackupType", "Normal")
                    selected = row.get("selected", "False").lower() in ("true", "1", "yes")
                    if row["task_name"] != current_task:
                        other_entries.append((
                            row["task_name"],
                            row["source"],
                            row["backup"],
                            backup_type,
                            selected
                        ))
        # Combine other_entries and new_entries (new_entries overwrites all same task_name)
        all_entries = other_entries + new_entries
        with open(GRID_CSV, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["task_name", "source", "backup", "selected", "BackupType"])
            for task, src, dst, backup_type, selected in all_entries:
                writer.writerow([task, src, dst, str(selected), backup_type])
        self.load_task_list_from_csv()
        messagebox.showinfo("Task", "Paths and task names saved to CSV.\nTask list refreshed on right.")
        self.entries.clear()
        self.refresh_tree()
        self.reset_fields()

    def load_grid_from_csv(self):
        self.entries.clear()
        if not os.path.exists(GRID_CSV):
            return
        with open(GRID_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            all_entries = []
            for row in reader:
                backup_type = row.get("BackupType", "Normal")
                selected = row.get("selected", "False").lower() in ("true", "1", "yes")
                all_entries.append((
                    row["task_name"],
                    row["source"],
                    row["backup"],
                    backup_type,
                    selected
                ))
        if not all_entries:
            return
        first_task = all_entries[0][0]
        self.entries = [entry for entry in all_entries if entry[0] == first_task]
        self.refresh_tree()
        if self.entries:
            self.task_name.set(self.entries[0][0])
            self.source_path.set(self.entries[0][1])
            self.dest_path.set(self.entries[0][2])
            self.backup_type.set(self.entries[0][3])
            self.editing_index = 0

    def load_task_list_from_csv(self):
        self.task_list.delete(0, tk.END)
        tasks = set()
        if os.path.exists(GRID_CSV):
            with open(GRID_CSV, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if "task_name" in row and row["task_name"]:
                        tasks.add(row["task_name"])
        sorted_tasks = sorted(tasks)
        for task in sorted_tasks:
            self.task_list.insert(tk.END, task)
        if sorted_tasks:
            self.task_list.selection_set(0)
            self.task_list.activate(0)

    def on_task_select(self, event):
        selection = event.widget.curselection()
        if not selection:
            return
        selected_task = event.widget.get(selection[0])

        self.entries.clear()
        self.refresh_tree()
        for idx, (task, src, dst, backup_type, selected) in enumerate(self.load_entries_from_csv(selected_task)):
            self.entries.append((task, src, dst, backup_type, selected))
            if idx == 0:
                self.task_name.set(task)
                self.source_path.set(src)
                self.dest_path.set(dst)
                self.backup_type.set(backup_type)
                self.editing_index = 0
        self.refresh_tree()

    def load_entries_from_csv(self, task_name):
        entries = []
        if os.path.exists(GRID_CSV):
            with open(GRID_CSV, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    backup_type = row.get("BackupType", "Normal")
                    selected = row.get("selected", "False").lower() in ("true", "1", "yes")
                    if row["task_name"] == task_name:
                        entries.append((row["task_name"], row["source"], row["backup"], backup_type, selected))
        return entries
    
    def open_scheduler(self):
        # Get distinct list of tasks from CSV
        tasks = set()
        if os.path.exists(GRID_CSV):
            with open(GRID_CSV, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if "task_name" in row and row["task_name"]:
                        tasks.add(row["task_name"])
        child = TaskScheduleForm(self.root, sorted(tasks))
        child.transient(self.root)  # Makes window stay on top
        child.grab_set()            # Modal - blocks events to other windows
        self.root.wait_window(child) # Wait here until window is destroyed


    def remove_selected_task(self):
        selection = self.task_list.curselection()
        if not selection:
            messagebox.showwarning("Remove Selected", "Please select a task to remove.")
            return
        selected_task = self.task_list.get(selection[0])
        confirm = messagebox.askyesno("Confirm Delete", f"Delete all entries for task '{selected_task}'?")
        if not confirm:
            return

        # Read all tasks except those matching selected_task:
        remaining_entries = []
        if os.path.exists(GRID_CSV):
            with open(GRID_CSV, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get("task_name") != selected_task:
                        remaining_entries.append(row)

        # Write back to CSV without the removed task
        with open(GRID_CSV, "w", newline='') as csvfile:
            fieldnames = ["task_name", "source", "backup", "selected", "BackupType"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(remaining_entries)

        # Refresh UI
        self.load_task_list_from_csv()
        self.load_grid_from_csv()
        self.refresh_tree()
        self.reset_fields()
        messagebox.showinfo("Remove Selected", f"Deleted task '{selected_task}' successfully.")




if __name__ == "__main__":
    root = tk.Tk()
    app = FileCopyMasterPage(root)
    root.mainloop()
