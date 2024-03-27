step0:
	docker compose build

step1:
	docker compose run --rm misago python manage.py migrate

step2:
	docker compose run --rm misago python manage.py createsuperuser

step3:
	docker compose up

.PHONY: dev
