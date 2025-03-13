# Use an official Python image as a base
FROM cgr.dev/chainguard/python:latest-dev

# Set the working directory inside the container
WORKDIR /app

# Copy the bot files into the container
COPY ./src /app

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Ensure entry script has execution permissions
RUN chmod +x entry.sh

# Set the command to run the bot
CMD ["./src/entry.sh"]
