sudo docker build -f Dockerfile_es -t dataesr/es_icu -t dataesr/es_icu:1.0 .
sudo docker push dataesr/es_icu

sudo docker build -f Dockerfile -t dataesr/affiliation-matcher -t dataesr/affiliation-matcher:0.1.1 .
sudo docker push dataesr/affiliation-matcher

# docker-compose down && docker-compose pull && docker-compose up