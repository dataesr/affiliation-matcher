#sudo docker build -f Dockerfile_nginx -t dataesr/nginxcrawler -t dataesr/nginxcrawler:1.0 .
#sudo docker push dataesr/nginxcrawler

#sudo docker build -f Dockerfile_dashboard -t dataesr/dashboard-crawler -t dataesr/dashboard-crawler:1.0 .
#sudo docker push dataesr/dashboard-crawler

sudo docker build -f Dockerfile_requests -t dataesr/requests -t dataesr/requests:1.0 .
sudo docker push dataesr/requests

sudo docker build -f Dockerfile -t dataesr/pubmed -t dataesr/pubmed:1.1 .
sudo docker push dataesr/pubmed
