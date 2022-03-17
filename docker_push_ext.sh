sudo docker build -f Dockerfile_es -t dataesr/es_icu -t dataesr/es_icu:1.0 .
sudo docker push dataesr/es_icu

sudo docker build -f Dockerfile -t dataesr/matcher-affiliation -t dataesr/matcher-affiliation:0.1.1 .
sudo docker push dataesr/matcher-affiliation

# docker-compose down && docker-compose pull && docker-compose up