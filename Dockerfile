# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV MONGO_URI 
ENV client_id 
ENV client_secret 
# ENV API_KEY your_api_key_here

# Run app.py when the container launches
CMD ["python", "new_pn_validator.py"]

# export MONGO_URI="mongodb+srv://prithvi-dev:zJxvnJcrjbsObiKK@cluster0.yycvy.mongodb.net/?retryWrites=true&w=majority"
# export client_id=5fa94dc6d979443cb23af73061b191b0
# export client_secret=e2209552eb8b4614b74647ce0e2a06dd
