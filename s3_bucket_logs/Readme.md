tail -f /var/log/nginx/error.log /var/log/nginx/access.log

sudo vi /etc/nginx/nginx.conf


sudo systemctl reload nginx
sudo systemctl restart nginx

sudo vi /etc/nginx/sites-available/default


watch -n 1 "if systemctl is-active --quiet nginx; then echo 'Nginx is RUNNING'; else echo 'Nginx is STOPPED or FAILED'; fi"

timeout 20s bash -c 'while true; do curl -s localhost:80/afdsfd; sleep 1; done'