# Affiliation matcher

The affiliation matcher aims to automatically align an affiliation with different reference systems, including :
- [Country ISO 3166](https://en.wikipedia.org/wiki/ISO_3166)
- [ROR](https://ror.org/)
- [grid](https://grid.ac/)

And specifically for French affiliations :
- [RNSR (Répertoire National des Structures de Recherche)](https://appliweb.dgri.education.fr/rnsr/)
- [Siren](https://www.sirene.fr/sirene/public/accueil)
- [FINESS](https://www.data.gouv.fr/fr/datasets/finess-extraction-du-fichier-des-etablissements)

## Run it locally
```
git clone git@github.com:dataesr/matcher.git
cd matcher
docker-compose up -d
curl http://localhost:5004/init
```

In your browser you now have :
- Elasticsearch : http://localhost:9200/
- RabbitMQ : http://localhost:9181/
- Matcher : http://localhost:5004/
