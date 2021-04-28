# Affiliation matcher

![Tests](https://github.com/dataesr/matcher/actions/workflows/tests.yml/badge.svg)
![Build](https://github.com/dataesr/matcher/actions/workflows/build.yml/badge.svg)

The affiliation matcher aims to automatically align an affiliation with different reference systems, including :
- [Country ISO 3166](https://en.wikipedia.org/wiki/ISO_3166)
- [ROR](https://ror.org/)
- [grid](https://grid.ac/)

And specifically for French affiliations :
- [RNSR (Répertoire National des Structures de Recherche)](https://appliweb.dgri.education.fr/rnsr/)
- [Siren](https://www.sirene.fr/sirene/public/accueil)
- [FINESS](https://www.data.gouv.fr/fr/datasets/finess-extraction-du-fichier-des-etablissements)

## Run it locally
```shell
git clone git@github.com:dataesr/matcher.git
cd matcher
make start init
```

In your browser, you now have :
- Elasticsearch : http://localhost:9200/
- RabbitMQ : http://localhost:9181/
- Matcher : http://localhost:5004/

## Run unit tests

```shell
make test
```

## Build python package
To generate the tarball package into the dist folder
```shell
make python-build
```
To install the generated package into your project

```shell
pip install /path/to/your/package.tar.gz
```
Then import the package into your python file
```python
import matcher
```

## Release
It uses [semver](https://semver.org/).

To create a new release, do
```shell
make release VERSION=x.x.x
```