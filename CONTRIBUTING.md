## Building and Running the Docker Image

This section explains how to build and run a Docker image for the project. This is useful for local development and testing.

### Prerequisites

Before you begin, make sure you have Docker installed on your system.

### Building the Docker Image

1. **Clone the repository:**

   Start by cloning the project repository to your local machine:

   ```bash
   git clone https://github.com/piglei/ai-vocabulary-builder.git
   cd ai-vocabulary-builder
   ```

2. **Build the Docker image:**

   Navigate to the root directory of the cloned repository and run the following command to build the Docker image. This command uses the `Dockerfile` in the current directory to create an image named `my-vocabulary-builder`.

   ```bash
   docker build -t my-vocabulary-builder .
   ```

### Running the Docker Image

Once the image is built, you can run it using the following command:

```bash
docker run -d -p 16093:16093 -v ~/.aivoc_db:/root/.aivoc_db:Z my-vocabulary-builder
```

or not default port

```bash
docker run -d -p 9000:16093 -v ~/.aivoc_db:/root/.aivoc_db:Z my-vocabulary-builder
```

Let's break down this command:

* **`docker run`**: This command starts a container from the specified image.
* **`-d`**: This runs the container in detached mode, meaning it runs in the background.
* **`-p 16093:16093`**: This maps port 16093 on your host machine to port 16093 in the container.
* **`-v ~/.aivoc_db:/root/.aivoc_db:Z`**: This mounts a volume. This is important for persisting your data.
    * **`~/.aivoc_db`**: This is the path to the database directory on your host machine.
    * **`/root/.aivoc_db`**: This is the path to the database directory inside the Docker container.
    * **`:Z`**: This is a SELinux-specific mount option (if applicable). It tells Docker to label the volume with a shared context. If you're not using SELinux, you might not need this or may need a different option. **It's important to understand if this `:Z` is necessary for your specific setup. If you are not using SELinux, it might be removable or require a different flag.**
* **`my-vocabulary-builder`**: This is the name of the Docker image you built in the previous step.

### Accessing the Application

After running the container, you can access the application in your web browser by navigating to:

```
http://127.0.0.1:16093/
```
