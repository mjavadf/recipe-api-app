# use PowerShell instead of sh:
set shell := ["powershell.exe", "-c"]

# Run django development server
runserver:
    @docker-compose run --rm app sh -c "python manage.py runserver"

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
    docker-compose run --rm app sh -c "python manage.py migrate {{app}}"

# Run shell in the app container
shell:
    docker-compose run --rm app sh -c "python manage.py shell -i ipython"

# Run manage.py commands
manage +command:
    docker-compose run --rm app sh -c "python manage.py {{command}}"