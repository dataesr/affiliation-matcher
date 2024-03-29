# Affiliation matcher

[![Discord Follow](https://dcbadge.vercel.app/api/server/TudsqDqTqb?style=flat)](https://discord.gg/TudsqDqTqb)
![license](https://img.shields.io/github/license/dataesr/affiliation-matcher)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/dataesr/affiliation-matcher?display_name=tag)
![Tests](https://github.com/dataesr/affiliation-matcher/actions/workflows/tests.yml/badge.svg)
![Build](https://github.com/dataesr/affiliation-matcher/actions/workflows/build.yml/badge.svg)

## Goal

The affiliation matcher aims to automatically align an affiliation with different reference systems, including :

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

:warning: Please use `docker-compose` version 1.27.0 up to 1.19.2.


```shell
git clone git@github.com:dataesr/affiliation-matcher.git
cd affiliation-matcher
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

In python, you can call the matcher this way:

```shell
import requests
url = 'http://localhost:5004/match'
r=requests.post(url, json={
  "type": "ror", 
  "name": "Paris Dauphine University", 
  "city": "Paris",
  "country": "France",
  "verbose": False}
)
r.json()
```

For RoR, available criteria are: id, grid_id, name, city, country, supervisor_name, acronym, city_zone_emploi, city_nuts_level2, web_url, web_domain. Default strategies are detauked https://github.com/dataesr/affiliation-matcher/blob/master/project/server/main/match_ror.py

For RNSR, available criteria are: year, id, code_number, acronym, name, supervisor_name, supervisor_acronym, zone_emploi, city, web_url. Default strategies are detailed in https://github.com/dataesr/affiliation-matcher/blob/master/project/server/main/match_rnsr.py

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
import affiliation-matcher
```

## Release

It uses [semver](https://semver.org/).

To create a new release:
```shell
make release VERSION=x.x.x
```

## API

### Match a single query `/match`

Query the API by setting your own strategies :

`curl "YOUR_API_IP/match" -X POST -d '{"type": "YOUR_TYPE", "query": "YOUR_QUERY", "strategies": "YOUR_STRATEGIES", "year": "YOUR_YEAR"}'`

YOUR_TYPE is optional, has to be a string and can be one of :
* "country"
* "grid"
* "rnsr"
* "ror"

By default, YOUR_TYPE is equal to "rnsr".

YOUR_QUERY is **mandatory**, has to be a string and is your affiliation text.

By example : `IPAG Institut de Planétologie et d'Astrophysique de Grenoble`.

YOUR_STRATEGIES is optional, has to be a 3 dimensional arrays of criteria (see next paragraph).

By example : `[[["grid_name", "grid_country"], ["grid_name", "grid_country_code"]]]`.

YOUR_YEAR is optional, and can be used only if you use the "rnsr" matcher type, has te be a string.

By example : `1998`.

By default, YOUR_YEAR is not set ie. it will be match over all years.


### Match multiple queries `/match_list`

`curl "YOUR_API_IP/match_list" -X POST -d '{"match_types": "YOUR_TYPES", "affiliations": "YOUR_AFFILIATIONS"}'`

YOUR_TYPES is optional, has to be a list of string and can contain one of :
* "country"
* "grid"
* "rnsr"
* "ror"

By default, YOUR_TYPES is equal to ["grid", "rnsr"].

YOUR_AFFILIATIONS is optional, has to be a list of string.
By example : `["affiliation_01", "affiliation_02"]`.

By default, YOUR_AFFILIATIONS is equal to [].


## Criteria

Here is a list of the criteria available for the **country matcher**:
* country_alpha3
* country_name
* country_subdivision_code
* country_subdivision_name

Here is a list of the criteria available for the **grid matcher**:
* grid_acronym
* grid_acronym_unique
* grid_cities_by_region [indirect]
* grid_city
* grid_country
* grid_country_code
* grid_department
* grid_id
* grid_name
* grid_name_unique
* grid_parent
* grid_region

Here is a list of the criteria available for the **rnsr matcher**:
* rnsr_acronym
* rnsr_city
* rnsr_code_number
* rnsr_code_prefix
* rnsr_country_code
* rnsr_id
* rnsr_name
* rnsr_name_txt
* rnsr_supervisor_acronym
* rnsr_supervisor_name
* rnsr_urban_unit
* rnsr_web_url
* rnsr_year
* rnsr_zone_emploi [indirect]

Here is a list of the criteria available for the **ror matcher**:
* ror_acronym
* ror_acronym_unique
* ror_city
* ror_country
* ror_country_code
* ror_grid_id
* ror_id
* ror_name
* ror_name_unique

1. You can combine criteria to create a strategy.
2. You can cumulate strategies to create a family of strategies.
3. And then you can cumulate families of strategies to create the final object.
4. This final object `strategies` is then a 3 dimensional array that you will give as an argument to the "/match" API endpoint.
By example : `[[["grid_name", "grid_country"], ["grid_name", "grid_country_code"]]]`.


## Results

| matcher | precision | recall |
| ----- | ----- | ----- |
| country | 0.9953 | 0.9690 |
| grid | 0.7946 | 0.5944 |
| rnsr | 0.9654 | 0.8192 |
| ror | 0.8891 | 0.2356 | (TBC ???)
