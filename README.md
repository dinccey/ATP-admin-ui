# ATP-admin-ui
Admin UI for ATP

Copy .env.example to .env and modify needed values

Build:

```
cd ATP-admin-ui
podman build -t atp-admin .

podman run -d --name atp-admin -p 8001:8001 --env-file .env -v /your/host/fs/path:/data:Z atp-admin:latest
```

Modify ALLOWED_HOSTS if needed for the right IP

```
ALLOWED_HOSTS = [
    '192.168.100.10', 
    # Or for broader access (dev only!): '*'
]
```

upgrade on the server

```
git pull

podman build -t atp-admin .

podman run --replace -d --restart=always --name atp-admin -p 8001:8001 --env-file .env -v /home/shared/video:/video:Z atp-admin:latest

```