# fastapi_ecommerce

Python 3.12

## Clone the Repository

To get started, clone the project repository using Git:

```bash
git clone https://github.com/dvs-25/fastapi_ecommerce.git
cd fastapi_ecommerce
```

## Create a Virtual Environment

It's recommended to use a virtual environment to manage project dependencies. Follow the instructions for your operating
system:

### Linux / MacOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## Install Dependencies

Once the virtual environment is activated, install the project dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Create Database

```bash
alembic upgrade head
```

## Run server

```bash
uvicorn app.main:app --reload
```



- By default, services will be available at: http://localhost:8000
- Swagger -  http://localhost:8000/docs
