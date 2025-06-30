# ---------------------------
# Config
# ---------------------------
PROJECT_NAME = traffic-api
SERVICE_NAME = web
DB_SERVICE = db
DOCKER_COMPOSE = docker-compose
ETL_SCRIPT = etl/ingest_parquet.py

# ---------------------------
# Commands
# ---------------------------

up:
	@echo "🚀 Starting Docker containers..."
	$(DOCKER_COMPOSE) up --build -d

down:
	@echo "🛑 Stopping Docker containers..."
	$(DOCKER_COMPOSE) down

logs:
	@echo "📜 Tailing logs for $(SERVICE_NAME)..."
	$(DOCKER_COMPOSE) logs -f $(SERVICE_NAME)

etl:
	@echo "📥 Running ETL to load Parquet files into PostGIS..."
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) python $(ETL_SCRIPT)

psql:
	@echo "🔍 Opening PostgreSQL psql shell..."
	$(DOCKER_COMPOSE) exec $(DB_SERVICE) psql -U user -d trafficdb

bash:
	@echo "🧑‍💻 Entering shell in $(SERVICE_NAME)..."
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) bash

jupyter:
	@echo "📓 Starting Jupyter Notebook (port 8888)..."
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser

clean:
	@echo "🧹 Removing all containers and volumes..."
	$(DOCKER_COMPOSE) down -v

rebuild:
	@echo "🔁 Rebuilding containers..."
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up --build -d

help:
	@echo ""
	@echo "📦 Urban SDK Microservice - Makefile Commands:"
	@echo "---------------------------------------------"
	@echo "  make up         - Start all containers"
	@echo "  make down       - Stop all containers"
	@echo "  make logs       - Tail FastAPI logs"
	@echo "  make etl        - Run ETL to load parquet files into DB"
	@echo "  make psql       - Open psql shell in PostGIS container"
	@echo "  make bash       - Open bash shell in app container"
	@echo "  make jupyter    - Start Jupyter server"
	@echo "  make clean      - Remove containers and volumes"
	@echo "  make rebuild    - Rebuild containers and restart"
	@echo "  make help       - Show this message"
	@echo ""

