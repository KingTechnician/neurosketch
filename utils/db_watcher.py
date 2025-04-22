import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer, Lock
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DBFileHandler(FileSystemEventHandler):
    def __init__(self, callback_function, debounce_seconds=1):
        self.callback_function = callback_function
        self.debounce_seconds = debounce_seconds
        self.last_modified = time.time()
        self.timer = None
        self.timer_lock = Lock()
        
    def on_modified(self, event):
        if not event.is_directory:
            # Only trigger on main db file changes, ignore WAL and SHM
            if event.src_path.endswith('.db'):
                self._debounce_callback()
    
    def _debounce_callback(self):
        """Debounce the callback to prevent multiple rapid executions"""
        with self.timer_lock:
            current_time = time.time()
            
            # Cancel any existing timer
            if self.timer:
                self.timer.cancel()
            
            # Create new timer
            self.timer = Timer(self.debounce_seconds, self._execute_callback)
            self.timer.start()
    
    def _execute_callback(self):
        """Execute the callback function"""
        try:
            self.callback_function()
        except Exception as e:
            print(f"Error in database change callback: {e}")

def setup_db_watcher(callback_function, debounce_seconds=1):
    """
    Set up a file system watcher for the database file.
    
    Args:
        callback_function: Function to call when database file changes
        debounce_seconds: Number of seconds to wait before triggering callback
                         after a change is detected (default: 1)
    
    Returns:
        Observer instance that can be used to stop the watcher
    """
    path_to_db = os.getenv("PATH_TO_DB")
    if not path_to_db:
        raise ValueError("PATH_TO_DB environment variable not set")
    
    # Get the directory containing the database file
    path_dir = os.path.dirname(path_to_db)
    if not path_dir:  # If PATH_TO_DB is just a filename
        path_dir = "."
        
    # Create and start the observer
    event_handler = DBFileHandler(callback_function, debounce_seconds)
    observer = Observer()
    observer.schedule(event_handler, path_dir, recursive=False)
    observer.start()
    
    return observer
