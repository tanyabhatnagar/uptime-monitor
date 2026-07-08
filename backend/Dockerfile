# Use official slim Python 3.12 image for high-performance and small footprint
FROM python:3.12-slim

# Set environment variables
# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout/stderr (essential for logs)
ENV PYTHONUNBUFFERED=1

# Set the container working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy all backend app source files to container
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Command to run application via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
