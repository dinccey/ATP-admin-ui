# ATP-admin-ui
Admin UI for ATP

Copy .env.example to .env and modify needed values

Build:

```
cd ATP-admin-ui
podman build -t atp-admin .

podman run -d --name atp-admin -p 8001:8001 --env-file .env -v /your/host/fs/path:/data:Z atp-admin:latest
```

