# Matcher affiliations

![Tests](https://github.com/dataesr/matcher-affiliation/actions/workflows/tests.yml/badge.svg)
![Build](https://github.com/dataesr/matcher-affiliation/actions/workflows/build.yml/badge.svg)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/dataesr/matcher-affiliation?display_name=tag)

## Goal

The matcher affiliations aims to automatically align an affiliation with different reference systems, including :

- [Country ISO 3166](https://en.wikipedia.org/wiki/ISO_3166)
- [grid](https://grid.ac/)
- [ROR](https://ror.org/)
- [Wikidata](https://www.wikidata.org/)

And specifically for French affiliations :

- [FINESS](https://www.data.gouv.fr/fr/datasets/finess-extraction-du-fichier-des-etablissements)
- [RNSR (Répertoire National des Structures de Recherche)](https://appliweb.dgri.matchereducation.fr/rnsr/)
- [Siren](https://www.sirene.fr/sirene/public/accueil)

## Methodology

The methodology is fully explained in a publication freely available on HAL:
https://hal.archives-ouvertes.fr/hal-03365806.

## Run it locally

```shell
git clone git@github.com:dataesr/matcher-affiliation.git
cd matcher-affiliation
make docker-build start
```

Wait for Elasticsearch to be up. Then run :

```shell
make load
```

In your browser, you now have :

- Elasticsearch : http://localhost:9200/
- RabbitMQ : http://localhost:9181/
- Matcher : http://localhost:5004/

## Run unit tests

```shell
make test
```

## Build docker image

```shell
make docker-build
```

## Build python package

To generate the tarball package into the **dist** folder :

```shell
make python-build
```

To install the generated package into your project :

```shell
pip install /path/to/your/package.tar.gz
```

Then import the package into your python file

```python
import matcher-affiliation
```

## Release

It uses [semver](https://semver.org/).

To create a new release:
```shell
make release VERSION=x.x.x
```

## API

Querying the API but setting your own strategies :

`curl "YOUR_API_IP" -X POST -d '{"type": "grid", "query": "YOUR_QUERY", "strategies": [[["grid_name", "grid_country"], ["grid_name", "grid_country_code"]]]}'`


## Criteria

Here is a list of the 9 criteria available for the Grid matcher:
* grid_acronym
* grid_cities_by_region [indirect]
* grid_city
* grid_country
* grid_country_code
* grid_department
* grid_name
* grid_parent
* grid_region


1. You can combine criteria to create a strategy.
2. You can cumulate strategies to create a family of strategies.
3. And then you can cumulate families of strategies to create the final object.
4. This final object is then a 3 dicmensional array that you will give as an argument to the "/match_api" API endpoint.