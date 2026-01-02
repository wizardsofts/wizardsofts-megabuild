# Setup Centralized Microservice Infrastructure

This guide provides step-by-step instructions to set up the centralized microservice infrastructure using Docker Swarm and Traefik.

## 1. Prerequisites

- You have 3 servers available. One will be the manager node, and the other two will be worker nodes.
- Docker is installed on all 3 servers.
- You have SSH access to all 3 servers.

## 2. Set up Docker Swarm

You need to initialize Docker Swarm on your manager node and then have your other nodes join the swarm as workers.

### On your designated **manager** node:

1.  **Initialize Docker Swarm:**

    Open a terminal on your manager node and run the following command. Replace `<MANAGER_IP>` with the actual IP address of the manager node. This is the IP that worker nodes will use to connect to the manager.

    ```bash
    docker swarm init --advertise-addr <MANAGER_IP>
    ```

2.  **Get the worker join token:**

    After the swarm is initialized, Docker will output a command to join worker nodes. It will look something like this:

    ```
    docker swarm join --token <YOUR_TOKEN> <MANAGER_IP>:2377
    ```

    Copy this entire command. You will need it for the worker nodes.

    If you ever need to retrieve this command again, you can run the following on the manager node:
    ```bash
    docker swarm join-token worker
    ```

### On each of your **worker** nodes:

1.  **Join the Swarm:**

    Open a terminal on each worker node and paste the `docker swarm join` command you copied from the manager. It will look like this:

    ```bash
    docker swarm join --token <YOUR_TOKEN> <MANAGER_IP>:2377
    ```

    After running this command, the node will be part of the swarm.

2.  **Verify the cluster:**

    Once all nodes have joined, you can go back to your **manager** node and run the following command to see all the nodes in your swarm:

    ```bash
    docker node ls
    ```

    You should see all 3 of your servers listed.

## 3. Deploy the Traefik Reverse Proxy

Now that your swarm is ready, you can deploy Traefik. Traefik will act as the reverse proxy and entry point for all your services.

### On your **manager** node:

1.  **Clone this repository:**

    If you haven't already, clone this repository to your manager node.

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Deploy the Traefik stack:**

    From the root of the repository, run the following command:

    ```bash
    docker stack deploy -c docker-compose.yml traefik
    ```

    This command will create a new stack named `traefik` and deploy the services defined in the `docker-compose.yml` file. The `microservices-overlay` network will also be created, allowing services to communicate with each other across the swarm.

3.  **Verify the deployment:**

    To check that the Traefik service is running, use this command:

    ```bash
    docker service ls
    ```

    You should see a service named `traefik_traefik` with 1/1 replicas.

4.  **Access the Traefik Dashboard:**

    The Traefik dashboard is exposed on port 8080. You can access it by navigating to `http://<MANAGER_IP>:8080` in your web browser.

    The dashboard is configured to be accessible at `http://traefik.localhost`. To access it, you need to either:

    -   **Use a local DNS entry:** Add an entry to your local `/etc/hosts` file (on your computer, not the server) to map `traefik.localhost` to your manager's IP address:
        ```
        <MANAGER_IP> traefik.localhost
        ```
        Then you can access the dashboard at `http://traefik.localhost:8080`.

    -   **Use a browser extension:** Use a browser extension that allows you to modify request headers and set the `Host` header to `traefik.localhost`.


## Next Steps

With the swarm and Traefik running, you can now start deploying your microservices. You will need to add them as services to the `docker-compose.yml` file or create new `docker-compose` files for them.

Remember to add the necessary labels to your services so that Traefik can discover them and route traffic to them.
