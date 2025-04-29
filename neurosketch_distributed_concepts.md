# Neurosketch: Parallel and Distributed Computing Implementation

## Overview

Neurosketch is a collaborative drawing application that implements several key concepts from parallel and distributed computing. This document outlines how the current implementation addresses these concepts and provides code examples from the existing codebase.

## Multiprocessing

**Current Implementation:**
- The FastAPI backend uses Uvicorn's worker processes to handle multiple requests concurrently
- In `backend/app/main.py`, when running with `uvicorn.run(app, host="0.0.0.0", port=8000)`, Uvicorn can spawn multiple worker processes
- The LLM integration in `backend/app/routes/generate.py` processes drawing generation requests independently
- Each drawing generation task is a separate process that doesn't block other operations

**Code Evidence:**
```python
# In backend/app/main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Can use multiple workers
```

## Multithreading

**Current Implementation:**
- The database watcher in `utils/db_watcher.py` runs in a separate thread to monitor database changes
- In `frontend/app.py`, the cleanup handler uses threading to manage resources
- The Streamlit application uses background threads for UI updates and state management
- The `on_db_change()` function in `frontend/app.py` triggers UI updates from a background thread

**Code Evidence:**
```python
# In utils/db_watcher.py
observer = Observer()
observer.schedule(event_handler, path_dir, recursive=False)
observer.start()  # Starts a background thread

# In frontend/app.py
def cleanup_resources():
    if "db_watcher" in st.session_state:
        try:
            st.session_state["db_watcher"].stop()
            st.session_state["db_watcher"].join()
        except Exception as e:
            print(f"Error stopping database watcher: {e}")

atexit.register(cleanup_resources)  # Thread management
```

## Interprocess Communication

**Current Implementation:**
- The frontend and backend communicate via HTTP requests (seen in `frontend/app.py` when making API calls)
- The SQLite database serves as a shared state mechanism between processes
- The watchdog module in `utils/db_watcher.py` monitors file changes to enable cross-process notifications
- The `save_canvas_changes()` function in `frontend/app.py` writes to the database, which other processes can then read

**Code Evidence:**
```python
# In frontend/app.py - HTTP communication with backend
response = requests.post("http://localhost:8000/generate", json=generate_request_obj, headers=headers)

# In utils/db_watcher.py - File-based IPC
class DBFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            if event.src_path.endswith('.db'):
                self._debounce_callback()
```

## Distributed Computing over Networked Machines

**Current Implementation:**
- The architecture separates frontend (Streamlit) and backend (FastAPI) components that can run on different machines
- The shared SQLite database enables state synchronization across machines
- The system uses HTTP for cross-machine communication
- The identity management system in `frontend/identity_utils.py` supports distributed user authentication

**Code Evidence:**
```python
# In frontend/app.py - Remote API calls that can target different machines
response = requests.post("http://localhost:8000/generate", json=generate_request_obj, headers=headers)

# In backend/app/main.py - Server binding that allows network access
uvicorn.run(app, host="0.0.0.0", port=8000)  # Accessible from network
```

## Internode Communication

**Current Implementation:**
- The backend API provides endpoints for frontend-to-backend communication
- The database watcher enables indirect communication between nodes through file changes
- The RSA-based authentication system in `frontend/identity_utils.py` and `backend/app/routes/generate.py` enables secure communication
- The `process_canvas_changes()` function in `frontend/app.py` tracks changes that are communicated to other nodes

**Code Evidence:**
```python
# In backend/app/routes/generate.py - Secure communication with signature verification
public_key = user.public_key
try:
    public_key = rsa.PublicKey.load_pkcs1(public_key.encode())
    signature_bytes = base64.b64decode(auth_signature)
    request_data = json.dumps(request.dict(), sort_keys=True)
    rsa.verify(request_data.encode("utf-8"), signature_bytes, public_key)
```

## Summary

Neurosketch already implements several parallel and distributed computing concepts:

1. **Multiprocessing**: Through Uvicorn's worker processes and independent request handling
2. **Multithreading**: Via database watchers, background tasks, and UI update mechanisms
3. **Interprocess Communication**: Using HTTP requests and database-mediated state sharing
4. **Distributed Computing**: Through separation of frontend and backend components
5. **Internode Communication**: Via API endpoints and database change notifications


