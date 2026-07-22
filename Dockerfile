FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mcplex/ mcplex/

RUN pip install --no-cache-dir .

EXPOSE 8000

ENTRYPOINT ["mcplex"]
CMD ["serve", "--config", "config.yaml", "--host", "0.0.0.0", "--port", "8000"]
