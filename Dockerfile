# Use an official Python image as a base
FROM python:3.12-slim

# Create a nonroot user and group for security compatibility
RUN groupadd -g 65532 nonroot && \
    useradd -u 65532 -g nonroot -m -s /sbin/nologin nonroot

# Set the working directory inside the container
WORKDIR /app

# Copy the bot files into the container and set ownership to nonroot
COPY --chown=nonroot:nonroot ./src /app

# Switch to nonroot user
USER nonroot

# Add ~/.local/bin to PATH to ensure installed scripts are found
ENV PATH="/home/nonroot/.local/bin:${PATH}"

# Install dependencies in the user's home directory
RUN pip install --no-cache-dir --user -r /app/requirements.txt

# Set the command to run the bot
CMD ["python", "bot.py"]
