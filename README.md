

# buyFromMe

`buyFromMe` is an e-commerce platform built with FastAPI. This project allows users to browse and purchase products from various sellers.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- FastAPI
- Uvicorn
- PostgreSQL (or another preferred database)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/buyFromMe.git
   cd buyFromMe
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use `venv\Scripts\activate`
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Rename `.env-example` to `.env`:
   ```bash
   mv .env-example .env
   ```

5. Fill in the necessary fields in the `.env` file:
   ```
   EMAIL="YOUR_EMAIL"
   PASS="YOUR_PASSWORD"
   SECRET="YOUR_SECRET"
   ```

### Configuring Gmail for Email Sending

If you are using Gmail, your password is not your usual Gmail password. Follow these steps to generate an app password:

1. Go to the [Google Account Page](https://myaccount.google.com/).
2. Navigate to `Security` > `Signing in to Google` section.
3. Turn on `2-Step Verification`. You need this feature enabled.
4. Click on [App Passwords](https://myaccount.google.com/u/3/apppasswords) to generate a new app password for mail access.
5. Use this generated password in the `PASS` field in the `.env` file.

### Generating a Secret Key

Generate a secret key using Python's `secrets` module:
```python
import secrets
secrets.token_hex(20)
```
Use the generated key in the `SECRET` field in the `.env` file.

### Running the Application

1. Apply the database migrations:
   ```bash
   alembic upgrade head
   ```

2. Start the FastAPI application:
   ```bash
   uvicorn main:app --reload
   ```

### Accessing the API Documentation

You can access the Swagger UI documentation at:
```
http://127.0.0.1:8000/docs
```

### Registration Endpoint

To register a new user, you can use the following endpoint:

```python
@app.post("/registration")
async def register_user(username: str, email: str, password: str):
    # Registration logic here
```

- `username` - Required, unique, max length 20 characters
- `email` - Required, unique, max length 200 characters
- `password` - Required, max length 100 characters

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

