# fastapi_ecommerce

Python 3.12

## Clone the Repository

To get started, clone the project repository using Git:

```bash
git clone https://github.com/dvs-25/fastapi_ecommerce.git
cd fastapi_ecommerce
```

## Running with Docker Compose

The easiest way to run this application is with Docker Compose:

```bash
docker compose up -d --build
```

This command will:
- Build the Docker images
- Start the web service (FastAPI application) on port 8000
- Start the PostgreSQL database service

## Initialize the Database

After the containers are running, you need to initialize the database:

```bash
docker compose exec web alembic upgrade head
```

This command will create all necessary tables in the database.

## Verify Database Setup

You can verify that everything was created correctly by connecting to the database:

```bash
docker compose exec db psql --username=ecommerce_user --dbname=ecommerce_db
```

Then within the PostgreSQL shell, you can list databases:

```
\l
```

And list tables:

```
\dt
```

To exit the PostgreSQL shell, type:

```
\q
```

## Accessing the Application

- By default, services will be available at: http://localhost:8000
- Swagger documentation: http://localhost:8000/docs

## Alternative: Running Locally (without Docker)

If you prefer to run the application locally without Docker, follow these steps:

### Create a Virtual Environment

It's recommended to use a virtual environment to manage project dependencies. Follow the instructions for your operating system:

#### Linux / MacOS

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies

Once the virtual environment is activated, install the project dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Create Database

```bash
alembic upgrade head
```

### Run Server

```bash
uvicorn app.main:app --reload
```