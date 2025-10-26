# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir requests

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run proxy.py when the container launches
CMD ["python", "proxy.py"]
