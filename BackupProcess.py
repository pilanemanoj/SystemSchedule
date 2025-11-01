import csv
import os
import shutil
import zipfile
from datetime import datetime
from logger import log_message

SCHEDULE_CSV = "schedules.csv"
PATHS_CSV = "paths.csv"
LOG_CSV = "backup_log.csv"

log_message("Backup Process Started.")

def load_enabled_schedule():
    try:
        if not os.path.exists(SCHEDULE_CSV):
            log_message("No schedule CSV found")
            return None
        with open(SCHEDULE_CSV, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Enabled", "").strip().lower() == "yes":
                    return row
        return None
    except Exception as e:
        log_message(f"Error in load_enabled_schedule: {e}")
        return None

def load_tasks_for_schedule(selected_tasks):
    try:
        if not os.path.exists(PATHS_CSV):
            log_message("No paths CSV found")
            return []
        task_names = [t.strip() for t in selected_tasks.split(",") if t.strip()]
        matched_tasks = []
        with open(PATHS_CSV, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["task_name"] in task_names:
                    matched_tasks.append(row)
        return matched_tasks
    except Exception as e:
        log_message(f"Error in load_tasks_for_schedule: {e}")
        return []

def copy_folder(src, dst):
    try:
        if not os.path.exists(src):
            log_message(f"Source path '{src}' does not exist")
            return False, f"Source path '{src}' does not exist"
        if not os.path.exists(dst):
            os.makedirs(dst)
        for item in os.listdir(src):
            s_path = os.path.join(src, item)
            d_path = os.path.join(dst, item)
            if os.path.isdir(s_path):
                shutil.copytree(s_path, d_path, dirs_exist_ok=True)
            else:
                shutil.copy2(s_path, d_path)
        return True, "Copied successfully"
    except Exception as e:
        log_message(f"Error in copy_folder: {e}")
        return False, str(e)

def zip_folder(src, dst):
    try:
        if not os.path.exists(src):
            log_message(f"Source path '{src}' does not exist")
            return False, f"Source path '{src}' does not exist"
        if not os.path.isdir(src):
            log_message(f"Source path '{src}' is not a directory")
            return False, f"Source path '{src}' is not a directory"
        if not os.path.exists(dst):
            os.makedirs(dst)
        zip_path = os.path.join(dst, os.path.basename(src) + ".zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(src):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, src)
                    zipf.write(full_path, arcname=rel_path)
        return True, f"Zipped to: {zip_path}"
    except Exception as e:
        log_message(f"Error in zip_folder: {e}")
        return False, str(e)

def log_execution(task_name, source, dest, backup_type, status, message):
    try:
        is_new = not os.path.exists(LOG_CSV)
        with open(LOG_CSV, "a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(["DateTime","TaskName","Source","Destination","BackupType","Status","Message"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_name, source, dest, backup_type, status, message])
    except Exception as e:
        log_message(f"Error in log_execution: {e}")

def main():
    try:
        schedule = load_enabled_schedule()
        if schedule is None:
            log_message("No enabled schedule found")
            return
        log_message(f"Running schedule: {schedule['Schedule Name']}")
        tasks = load_tasks_for_schedule(schedule.get("Selected Tasks", ""))
        if not tasks:
            log_message("No matching tasks found for schedule")
            return
        for t in tasks:
            task_name = t["task_name"]
            source = t["source"]
            dest = t["backup"]
            backup_type = t.get("BackupType", "normal").lower()
            log_message(f"Running task: {task_name} (Backup type: {backup_type})")
            if backup_type == "zip":
                status, msg = zip_folder(source, dest)
            else:
                status, msg = copy_folder(source, dest)
            log_execution(task_name, source, dest, backup_type, "Success" if status else "Failed", msg)
            log_message(f"Task {task_name} completed: {msg}")
    except Exception as e:
        log_message(f"Error in main: {e}")

if __name__ == "__main__":
    main()
