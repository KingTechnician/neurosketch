# Running Neurosketch

## Frontend

### Create a Python environment under the 'frontend' folder (Make sure you are in that folder)

```bash
python -m venv frontend_env
```

### Activate the environment

In Windows:

```bash
frontend_env\Scripts\activate
```

In Linux/Mac:

```bash
source frontend_env/bin/activate
```

### Install the required packages

```bash
pip install -r requirements.txt
```



## Backend

### Create a Python environment under the 'backend' folder (Make sure you are in that folder)

```bash 
python -m venv backend_env
```

### Activate the environment

In Windows:

```bash
backend_env\Scripts\activate
```

In Linux/Mac:

```bash
source backend_env/bin/activate
```

### Install the required packages

```bash
pip install -r requirements.txt
```

### Run the backend server

```bash
python -m app.main
```

### To run the tests (Hello World test as an example)

```bash
pytest tests/test_hello_world.py
```


## Database

Not implemented yet
