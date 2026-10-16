# Docker Volumes on Linux, Windows, and Docker Desktop

## Introduction

With this entry in `docker-compose.yml`:

```yaml
volumes:
  - mlflow-data:/mlflow
```

`mlflow-data` is a **named Docker volume**, and `/mlflow` is the path where the volume is mounted inside the MLflow container.

In this MLflow setup, the files are normally stored inside the container at:

```text
/mlflow/mlflow.db
/mlflow/artifacts/
```

- `mlflow.db` is the MLflow SQLite backend database.
- `artifacts/` contains experiment artifacts such as models, plots, metrics, and uploaded files.

---

## 1. Container versus volume

A container and a volume are separate objects:

| Item | Purpose | Normally remains after the container is removed? |
|---|---|---|
| Container | Runs the MLflow application | No |
| Named volume | Stores the database and artifacts | Yes |
| Bind mount | Connects a local folder to a container folder | Yes, because the files are in the local folder |

This command normally removes containers but preserves named volumes:

```cmd
docker compose down
```

This command removes containers **and** the Compose-managed volumes:

```cmd
docker compose down -v
```

These commands can also delete the data:

```cmd
docker volume rm mlops_project01_revised_mlflow-data
docker volume prune
```

> **Warning:** Do not use `docker compose down -v` or `docker volume rm` until you have confirmed that you no longer need the data.

---

## 2. Where is the named volume?

The volume name in this project is probably:

```text
mlops_project01_revised_mlflow-data
```

Check the exact name with:

```cmd
docker volume ls
```

Inspect its details with:

```cmd
docker volume inspect mlops_project01_revised_mlflow-data
```

The output may contain:

```text
Mountpoint: /var/lib/docker/volumes/mlops_project01_revised_mlflow-data/_data
```

This is a **Linux path inside Docker's storage environment**. It means that Docker stores the volume's data in the volume's `_data` directory.

The way you access that path depends on the operating system.

---

## 3. Native Linux: direct access

On a native Linux machine running Docker Engine directly, the path normally exists on the Linux filesystem:

```text
/var/lib/docker/volumes/mlops_project01_revised_mlflow-data/_data/
```

You can inspect it directly from a terminal:

```bash
sudo ls -lah /var/lib/docker/volumes/mlops_project01_revised_mlflow-data/_data
```

To list files recursively:

```bash
sudo find /var/lib/docker/volumes/mlops_project01_revised_mlflow-data/_data -type f -print
```

You may see files such as:

```text
/var/lib/docker/volumes/mlops_project01_revised_mlflow-data/_data/mlflow.db
/var/lib/docker/volumes/mlops_project01_revised_mlflow-data/_data/artifacts/...
```

### Why is `sudo` usually needed?

Docker normally owns these files, and their permissions are often restricted to `root`. Therefore, `sudo` is commonly needed to inspect them.

### Important note

Even on Linux, avoid manually editing files inside `/var/lib/docker`. It is safer to access the data through Docker commands because direct changes can cause permission problems or data corruption.

---

## 4. Windows with Docker Desktop

When Docker Desktop runs on Windows, Docker usually runs inside a Linux environment, commonly through WSL 2 or a Docker Desktop virtual machine.

Therefore, this path:

```text
/var/lib/docker/volumes/mlops_project01_revised_mlflow-data/_data
```

does **not** mean that this Windows path exists:

```text
C:\var\lib\docker\volumes\...
```

The path exists inside Docker Desktop's internal Linux storage, not as a normal Windows folder that File Explorer can browse.

Docker Desktop may store the underlying data inside a virtual disk such as:

```text
C:\Users\<WindowsUser>\AppData\Local\Docker\wsl\data\docker_data.vhdx
```

However, `.vhdx` is a virtual disk file, not an ordinary folder. **Do not edit or manipulate it directly**, because doing so can damage Docker Desktop or the stored data.

You can view available WSL distributions with:

```cmd
wsl -l -v
```

Docker Desktop's internal distribution and storage layout can change between versions, so do not rely on a particular internal distribution name or path.

### Recommended Windows method: access the volume through Docker

Run this from Command Prompt:

```cmd
docker run --rm -it ^
  -v mlops_project01_revised_mlflow-data:/data ^
  alpine sh
```

You are now inside a temporary Alpine Linux container. Run:

```sh
ls -lah /data
find /data -maxdepth 3 -type f -print
```

Inside this temporary container:

```text
/data
```

represents the contents of:

```text
/var/lib/docker/volumes/mlops_project01_revised_mlflow-data/_data
```

Exit with:

```sh
exit
```

You can also inspect the files without opening an interactive shell:

```cmd
docker run --rm ^
  -v mlops_project01_revised_mlflow-data:/data ^
  alpine sh -c "ls -lah /data && find /data -maxdepth 3 -type f -print"
```

> In PowerShell, use the backtick character `` ` `` for line continuation instead of `^`, or enter the command on one line.

---

## 5. What is Alpine?

**Alpine Linux** is a very small Linux distribution designed to be lightweight and fast. It is commonly used as a Docker image.

When you run:

```cmd
docker run --rm -it ^
  -v mlops_project01_revised_mlflow-data:/data ^
  alpine sh
```

Docker does the following:

1. Downloads the `alpine` image if it is not already available locally.
2. Creates a temporary container from that image.
3. Mounts the MLflow volume inside the container at `/data`.
4. Starts a shell named `sh`.
5. Automatically removes the temporary container when you exit because of `--rm`.

Removing this temporary container does **not** remove the volume. The volume is separate from the container.

Alpine is useful here because you do not need to run MLflow to inspect the files. You only need a small Linux environment that can read the volume.

Useful commands inside Alpine include:

```sh
ls -lah /data
find /data -maxdepth 3 -type f -print
```

---

## 6. Copy the volume data to Windows

If you want to browse the files normally in Windows File Explorer, copy them to a Windows folder.

From your project directory in Command Prompt, create the destination folder:

```cmd
mkdir mlflow-data
```

Then copy the data:

```cmd
docker run --rm ^
  -v mlops_project01_revised_mlflow-data:/mlflow ^
  -v "%cd%\mlflow-data:/backup" ^
  alpine sh -c "cp -a /mlflow/. /backup/"
```

After the command completes, the files should be available at:

```text
C:\Docs\Mehdi\Teaching\MLOps\python_code\mlops_project01_revised\mlflow-data
```

Possible contents include:

```text
C:\Docs\Mehdi\Teaching\MLOps\python_code\mlops_project01_revised\mlflow-data\mlflow.db
C:\Docs\Mehdi\Teaching\MLOps\python_code\mlops_project01_revised\mlflow-data\artifacts\
```

Verify the copy with:

```cmd
dir mlflow-data
dir mlflow-data\artifacts
```

You can open the folder in File Explorer with:

```cmd
explorer mlflow-data
```

If the volume name is different, first run:

```cmd
docker volume ls
```

Then replace the volume name in the copy command.

---

## 7. Make MLflow data permanently visible in Windows

If you want the data to live directly in your project folder, change the Compose mapping from:

```yaml
volumes:
  - mlflow-data:/mlflow
```

to:

```yaml
volumes:
  - ./mlflow-data:/mlflow
```

This is called a **bind mount**:

- `./mlflow-data` is a folder on Windows, relative to the Compose file.
- `/mlflow` is the path inside the MLflow container.

First copy the existing named volume into the local folder using the previous section. Verify the files. Then update the Compose file and recreate the service:

```cmd
docker compose down
docker compose up -d --build
```

After that, MLflow will use the files directly in:

```text
C:\Docs\Mehdi\Teaching\MLOps\python_code\mlops_project01_revised\mlflow-data
```

### Named volume versus bind mount

| Compose mapping | Where the data is visible to you |
|---|---|
| `mlflow-data:/mlflow` | Docker's internal storage |
| `./mlflow-data:/mlflow` | Directly in the Windows project folder |

---

## 8. Does deleting the container delete the data?

For a named volume, this command normally removes the containers but preserves the volume:

```cmd
docker compose down
```

When you start the project again:

```cmd
docker compose up -d --build
```

Docker attaches the same volume to the new MLflow container.

For a bind mount:

```yaml
- ./mlflow-data:/mlflow
```

the data is already stored in the Windows folder, so it remains even if the container is deleted and recreated.

---

## 9. Useful diagnostic commands

List all Docker volumes:

```cmd
docker volume ls
```

Inspect a volume:

```cmd
docker volume inspect mlops_project01_revised_mlflow-data
```

List files through Alpine:

```cmd
docker run --rm ^
  -v mlops_project01_revised_mlflow-data:/data ^
  alpine sh -c "find /data -maxdepth 3 -type f -print"
```

List running containers:

```cmd
docker ps
```

List all containers, including stopped containers:

```cmd
docker ps -a
```

List Compose services:

```cmd
docker compose ps
```

---

## 10. Summary

- On **native Linux**, a Docker named volume can normally be seen directly at:

  ```text
  /var/lib/docker/volumes/<volume-name>/_data
  ```

- On **Windows with Docker Desktop**, this path is inside Docker's internal Linux environment or virtual disk. It is not normally a Windows folder.
- On Windows, the safest way to inspect a named volume is to mount it into a temporary container, such as Alpine.
- **Alpine** is a small Linux distribution that is useful as a lightweight inspection container.
- Removing a container does not normally remove its named volume.
- `docker compose down -v` removes the volumes, so avoid it when the data is important.
- If you want the data to be visible in Windows all the time, use a bind mount:

  ```yaml
  volumes:
    - ./mlflow-data:/mlflow
  ```

- Before switching to a bind mount, copy and verify the existing named volume data.
