# Running Neurosketch

## [IMPORTANT NOTE]

**Regardless of the environment, in order to run the Neurosketch utils, do the following:**

Activate the environment (using either source or .\), make sure you are in the main directory, and run the following command:

```bash
pip install -e .
```

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

### Create a .env file in the 'frontend' folder with the following content:

```bash
PATH_TO_DB=<Path to the database file>
````




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

### Create a Python environment under the 'db' folder (Make sure you are in that folder)

```bash
python -m venv db_env
```

### Activate the environment

In Windows:

```bash
db_env\Scripts\activate
```

In Linux/Mac:

```bash
source db_env/bin/activate
```

### Install the required packages

```bash
pip install -r requirements.txt
```

### Run the database server

(TODO: Add instructions for running the database server when it is made))

