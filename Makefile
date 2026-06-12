# 互动百科 (baike) Makefile
# CD-30/32: smoke tests + docker 便捷命令

.PHONY: test smoke docker-build docker-run help

help:
	@echo "Available targets:"
	@echo "  make test         - Run full test suite (smoke + admin)"
	@echo "  make smoke        - Run smoke test only (tests/test_smoke.py)"
	@echo "  make docker-build - Build baike:latest image"
	@echo "  make docker-run   - Run container (requires DB_* env vars)"

test:
	pytest -v tests/

smoke:
	pytest -v tests/test_smoke.py

docker-build:
	docker build -t baike:latest .

docker-run:
	docker run --rm -p 8000:8000 \
		-e DB_HOST=$$DB_HOST \
		-e DB_PORT=$${DB_PORT:-3306} \
		-e DB_USER=$$DB_USER \
		-e DB_PASSWORD=$$DB_PASSWORD \
		-e DB_NAME=$${DB_NAME:-baike} \
		-e FLASK_SECRET=$$FLASK_SECRET \
		baike:latest
