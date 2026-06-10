# Use official Python — slim keeps the image small
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy the entire project into the container
COPY . .

# Make mygit.py executable
RUN chmod +x mygit/mygit.py

# Create a global shortcut inside the container
RUN echo '#!/bin/bash\npython3 /app/mygit.py "$@"' > /usr/local/bin/mygit \
    && chmod +x /usr/local/bin/mygit

# Default working directory for user projects
WORKDIR /workspace

# When the container starts, open a bash shell
CMD ["/bin/bash"]