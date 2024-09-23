# Use Python 3.12 as base image
FROM python:3.12-slim

# Set working directory in the container
WORKDIR /app

# Copy current directory contents into the container
COPY . /app

# Install Poetry
RUN pip install --upgrade pip
RUN pip install poetry

# Install dependencies
RUN poetry install --no-dev

# Expose port 8000
EXPOSE 8000

# Run the FastAPI app with Uvicorn
CMD ["poetry", "run", "uvicorn", "fast_llm_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
