sudo docker build -f Dockerfile_es -t dataesr/es_icu:latest -t dataesr/es_icu:7.12.0 .
sudo docker push dataesr/es_icu:latest
sudo docker push dataesr/es_icu:7.12.0

sudo docker build -f Dockerfile -t dataesr/affiliation-matcher:latest -t dataesr/affiliation-matcher:0.1.3 .
sudo docker push dataesr/affiliation-matcher:latest
sudo docker push dataesr/affiliation-matcher:0.1.3

# docker-compose down && docker-compose pull && docker-compose up