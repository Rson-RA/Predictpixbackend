# PredictPix - Cryptocurrency Prediction Platform

A cryptocurrency prediction betting platform powered by Pi Network. Users can create and participate in prediction markets using Pi cryptocurrency.

## Features

- Pi Network wallet authentication
- Create and participate in prediction markets
- Automatic settlement of predictions
- Admin approval workflow for new markets
- Comprehensive fee collection system
- Secure deposit and withdrawal through Pi wallet
- DDoS protection and rate limiting
- Detailed transaction logging
- Off-chain balance system

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Pi Network API Key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/predictpix.git
cd predictpix
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and configure it:
```bash
cp .env.example .env
```

5. Edit the `.env` file with your configuration values:
- Set your PostgreSQL database credentials
- Configure your Pi Network API key
- Set your security key
- Configure Redis connection
- Set allowed origins for CORS
- Adjust rate limiting and fee settings

6. Initialize the database:
```bash
alembic upgrade head
```

## Running the Application

1. Start the Redis server

2. Run the FastAPI application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## Project Structure

```
predictpix/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   ├── middleware.py
│   │   └── pi_auth.py
│   ├── db/
│   │   └── session.py
│   ├── models/
│   │   ├── base.py
│   │   └── models.py
│   └── main.py
├── alembic/
├── requirements.txt
├── .env.example
└── README.md
```

## Security Features

- Rate limiting middleware for DDoS protection
- Secure Pi Network wallet integration
- Environment-based configuration
- CORS protection
- Database connection pooling
- Request validation

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 