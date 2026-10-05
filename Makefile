.PHONY: run test

run:
	uvicorn main:app --reload --port 8000

test:
	pytest -q
