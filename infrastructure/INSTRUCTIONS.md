# Multi-Node Microservice Infrastructure Setup Instructions

This guide will walk you through setting up your three-server infrastructure using Docker Compose and an overlay network.

## Architecture Overview

*   **1x Gateway Node:** Runs Traefik, the reverse proxy and entry point for all traffic.
*   **2x Application Nodes:** Run your microservices.
*   **1x Overlay Network:** A special Docker network that connects all three servers, allowing containers to communicate securely across them.

## Prerequisites

1.  **Three Servers:** You should have three servers ready, with `ssh` access to each.
2.  **Docker and Docker Compose:** Ensure Docker and Docker Compose are installed on all three servers.
3.  **Maven (on your local machine):** You'll need Maven to build the sample Java application.
4.  **Open Ports:** Ensure that ports `80` and `443` are open on your **Gateway Node** and forwarded from your router if necessary.

---

## Step 1: Create the Overlay Network

This network allows containers across different hosts to communicate. You only need to create it on **one** of your servers. This server will host the "manager" components of the Swarm that manages the overlay network. Let's designate this as your **Gateway Node**.

1.  SSH into your chosen **Gateway Node**.
2.  Run the following command to initialize Docker Swarm. This is necessary to enable the multi-host overlay network.
    ```bash
    docker swarm init
    ```
    *Note: This command will output a token to join other nodes to the swarm. You can use this to have your other nodes join the swarm which will make managing the overlay network easier, but for this setup, we only need to initialize the swarm on one node to create the overlay network.*

3.  Create the overlay network:
    ```bash
    docker network create --driver overlay microservices-overlay
    ```

## Step 2: Deploy Traefik on the Gateway Node

On the same **Gateway Node**:

1.  If you haven't already, copy the `traefik` directory to this server.
2.  Navigate into the `traefik` directory:
    ```bash
    cd traefik
    ```
3.  Start Traefik:
    ```bash
    docker-compose up -d
    ```
4.  **Verify:** You should be able to access the Traefik dashboard by visiting your Gateway Node's IP address in a browser (e.g., `http://<GATEWAY_NODE_IP>:8080`).

## Step 3: Build the Sample Service

On your **local development machine**:

1.  Navigate to the `sample-service` directory:
    ```bash
    cd sample-service
    ```
2.  Build the Spring Boot application using Maven. This will create the `.jar` file that the `Dockerfile` needs.
    ```bash
    mvn clean package
    ```
    This will create a file at `target/demo-spring-boot-0.0.1-SNAPSHOT.jar`.

## Step 4: Deploy the Sample Service on an Application Node

Now, pick one of your other two servers to be an **Application Node**.

1.  SSH into your chosen **Application Node**.
2.  Run the following command to have this node join the swarm you created on the Gateway Node. Replace `<TOKEN>` and `<GATEWAY_NODE_IP>` with the output from the `docker swarm init` command you ran earlier.
    ```bash
    docker swarm join --token <TOKEN> <GATEWAY_NODE_IP>:2377
    ```
    *This allows the node to attach to the `microservices-overlay` network.*
3.  Copy the entire `sample-service` directory (including the `target` directory with the `.jar` file) to this server.
4.  Navigate into the `sample-service` directory:
    ```bash
    cd sample-service
    ```
5.  Start the service:
    ```bash
    docker-compose up -d
    ```

## Step 5: Test Everything

1.  **Check the service:** From your local machine, you can now access the sample service through the Traefik proxy. In your browser, visit `http://<GATEWAY_NODE_IP>/`. Because we set up the rule `Host(hello.localhost)`, you may need to edit your local `/etc/hosts` file to point `hello.localhost` to your `<GATEWAY_NODE_IP>`.
    Alternatively, you can send a `Host` header with `curl`:
    ```bash
    curl -H "Host: hello.localhost" http://<GATEWAY_NODE_IP>/
    ```
    You should see "Hello World!".

2.  **Check the Traefik Dashboard:** Refresh the Traefik dashboard. You should now see the `hello-world` service listed as a router and a service.

---

You have now successfully set up a multi-node microservice infrastructure! You can deploy more services on your Application Nodes by following the same pattern as the `sample-service`. Just make sure they attach to the `microservices-overlay` network.
