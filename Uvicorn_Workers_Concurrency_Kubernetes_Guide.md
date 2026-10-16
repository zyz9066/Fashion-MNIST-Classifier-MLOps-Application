# Uvicorn, Workers, Concurrency, Pods, and Kubernetes

## 1. Uvicorn

- **Uvicorn** is the web server that runs a FastAPI application.
- It receives HTTP requests and passes them to FastAPI.
- It can handle multiple requests concurrently, especially when requests spend time waiting for I/O.

```text
Client
  ↓
Uvicorn
  ↓
FastAPI
  ↓
Your API / ML model
```

## 2. Uvicorn Worker

- A **worker** is a separate Uvicorn/Python process.
- By default, Uvicorn normally runs with **one worker**.
- More workers can process more work at the same time.

```text
1 Container
├── Worker 1
├── Worker 2
├── Worker 3
└── Worker 4
```

### Benefits of more workers

- More requests can be processed in parallel.
- Can improve throughput for CPU-heavy work.
- One busy worker does not block the other worker processes.

### Cons of more workers

- Uses more CPU and RAM.
- Each worker is a separate process.
- An ML model may be loaded separately by each worker, increasing memory use.
- Scaling and failure management are less flexible than using separate Kubernetes Pods.

## 3. Concurrency

- **Concurrency** means having multiple requests/tasks in progress at the same time.
- One Uvicorn worker can still handle multiple concurrent requests.
- Concurrency does **not** necessarily mean that all requests are executing on the CPU at exactly the same time.

Example:

```text
1 Worker
├── Request A → waiting for database
├── Request B → being processed
└── Request C → waiting for another service
```

When one request is waiting, the worker can make progress on another request when the application is asynchronous or otherwise allows concurrency.

## 4. `--limit-concurrency`

Example:

```bash
uvicorn app.main:app --limit-concurrency 20
```

- Limits how many connections/tasks Uvicorn handles concurrently.
- Helps protect the application from too much simultaneous load.
- When the limit is reached, additional requests can receive **HTTP 503**.
- It is a **protection mechanism**, not a request queue.

```text
Limit = 20

Requests 1–20  → allowed
Request 21+    → HTTP 503
```

### Benefits

- Protects CPU and memory.
- Helps prevent overload during traffic spikes.
- Useful when ML inference is expensive.

### Cons

- Requests above the limit are rejected.
- A limit that is too low can reduce throughput.
- A limit that is too high may not protect the application enough.

## 5. Container

- A **container** packages the application and its dependencies.
- Example: your container may contain FastAPI, Uvicorn, Python packages, and the ML application.

```text
Container
└── FastAPI + Uvicorn + Application
```

## 6. Pod

- A **Pod is not a machine**.
- A Pod is a Kubernetes unit that runs one or more containers.
- For many simple applications, **one Pod contains one application container**.
- A Pod runs on a Kubernetes **Node**.

```text
Node (machine / VM)
└── Pod
    └── Container
        └── FastAPI + Uvicorn
```

## 7. Node

- A **Node** is the machine that runs Pods.
- It can be a physical server or a virtual machine.
- One Node can run many Pods.

```text
Node 1
├── Pod 1
├── Pod 2
└── Pod 3
```

## 8. Kubernetes Replicas

Instead of putting many workers inside one container, Kubernetes can run multiple Pods:

```text
Kubernetes
├── Pod 1 → Uvicorn → FastAPI → ML model
├── Pod 2 → Uvicorn → FastAPI → ML model
└── Pod 3 → Uvicorn → FastAPI → ML model
```

Each Pod is an independent application instance.

### Benefits of multiple Pods

- Kubernetes can distribute traffic across Pods.
- Failed Pods can be restarted.
- The number of Pods can be increased or decreased.
- Pods can be placed on different Nodes.
- Easier horizontal scaling.

### Cons

- More Pods require more CPU and memory.
- Each Pod may need its own copy of the ML model.
- More infrastructure and deployment complexity.

## 9. Workers vs Kubernetes Pods

| Feature | Uvicorn Workers | Kubernetes Pods |
|---|---|---|
| What is it? | Python processes | Application instances managed by Kubernetes |
| Where? | Inside one container | Inside containers running in Pods |
| Main purpose | More processes / throughput | Horizontal scaling and reliability |
| Scaling | Inside one container | Across Pods |
| Failure | Container failure affects all workers | Other Pods can continue |
| ML memory | Multiple model copies may exist | Each Pod may have a model copy |
| Autoscaling | Limited | Kubernetes supports autoscaling |

## 10. Simple Recommendation for an ML API

A common Kubernetes design is:

```text
Load Balancer
     ↓
┌────┼────┐
↓    ↓    ↓
Pod 1 Pod 2 Pod 3
 │     │     │
Uvicorn Uvicorn Uvicorn
1 worker 1 worker 1 worker
 │     │     │
Model Model Model
```

- Start with **one Uvicorn worker per container/Pod**.
- Use `--limit-concurrency` when you need protection from too many simultaneous requests.
- Let Kubernetes increase the number of Pods when more capacity is needed.
- Use multiple Uvicorn workers inside one container only when there is a clear reason and enough CPU/RAM.

## 11. Key Idea

```text
Uvicorn worker = one Python process

Concurrency = multiple requests/tasks in progress

--limit-concurrency = limit simultaneous work/connections

Container = packaged application

Pod = Kubernetes unit that runs container(s)

Node = machine / VM running Pods

Kubernetes replicas = multiple Pods for scaling
```
