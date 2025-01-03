# NordPool

Python script that sends Nordpool Day-ahead price reports via email.

Use `make` for deployment
```bash
sudo apt install make

make build # Build all containers
make run   # Start all containers (in background)
make stop  # Stop all started for development containers .
make clear # Clear all containers and all data
```

You need to pass these environment variables or use .env file:
- SMTP_LOGIN=<email>
- SMTP_PASSWORD=<password>