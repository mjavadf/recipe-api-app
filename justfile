# use PowerShell instead of sh:
set shell := ["powershell.exe", "-c"]

# Default command to run test and linter
@default:
    docker-compose run --rm app sh -c "python manage.py test && flake8"

# Run flake8 linter
lint:
    docker-compose run --rm app sh -c "flake8"

# Run tests
test:
    docker-compose run --rm app sh -c "python manage.py test"

# Make migrations for a specific app
makemigrations app="":
    docker-compose run --rm app sh -c "python manage.py makemigrations {{app}}"

# Apply migrations for a specific app
migrate app="":
    docker-compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate {{app}}"

# Run shell in the app container
shell:
    docker-compose run --rm app sh -c "python manage.py shell -i ipython"

# Run manage.py commands
manage +command:
    docker-compose run --rm app sh -c "python manage.py {{command}}"

# Start the application in detached modeusing docker-compose
up:
    docker-compose up -d

# Stop the application using docker-compose
down:
    docker-compose down

# Show the logs for the app container
logs *args:
    docker-compose logs {{args}}