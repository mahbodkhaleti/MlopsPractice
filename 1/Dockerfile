FROM python:3.11-slim

WORKDIR /app

# Copy package metadata
COPY pyproject.toml requirements.txt ./

# Copy source code
COPY src/ src/

# Install dependencies and package
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Default command
CMD ["airbnb-ops", "run"]
