# Use an official Python image as a base
FROM cgr.dev/chainguard/python:latest-dev

# Set the working directory inside the container
WORKDIR /app

# Copy the bot files into the container
COPY --chmod=+x ./src /app

# Add ~/.local/bin to PATH to ensure installed scripts are found
ENV PATH="/home/nonroot/.local/bin:${PATH}"

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set the command to run the bot
CMD ["bot.py"]
