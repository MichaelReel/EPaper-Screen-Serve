# Running E-Ink Service on an RPi Zero

Python requirements (on Raspberry Pi):

```shell
sudo apt install python3-flask
sudo apt install python3-gunicorn
sudo apt install python3-pillow
```

Proxy requirements (nginx):

```shell
sudo apt install nginx
```

Create a nginx configuration:

Where`<local-ip>` is something like `192.168.0.62`.

Create file: `/etc/nginx/sites-available/eink_service` with contents:

```nginx
server {
    listen 80;
    server_name <local-ip>;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable configuration:

```shell
sudo ln -s /etc/nginx/sites-available/flask_tutorial /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

Start service:

```shell
python3 -m gunicorn --bind 127.0.0.1:8080 server:app
```

From computer on the same network, point the browser to `http://<local-ip>` (something like `http://192.168.0.62`).