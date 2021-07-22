---
title: 'Using Elasticsearch for entity recognition in affiliation disambiguation'
author:
  - Anne L'Hôte:
      institute: mesri
  - Eric Jeangirard:
      institute: mesri
      orcid: 0000-0002-3767-7125
      idref: 242241344
institute:
  - mesri:
      name: 'French Ministry of Higher Education, Research and Innovation, Paris, France'
bibliography: matcher.bib
date: July 2021
keywords:
  - elasticsearch
  - affiliation disambiguation
---

**Keywords**: elasticsearch, affiliation disambiguation

# Abstract

# 1. Introduction

The precise identification of the affiliations found in the bibliographic databases is a crucial point in various 
aspects and in particular to follow the production of one or a group of laboratories or institutions, and thus be able
to observe trends related to publications at the institutional level.<br />

Unfortunately, this exercise remains a complex task, giving part of the value of paid bibliographic databases. 
Nevertheless, [@donner_comparing_2020] have shown that relying solely on commercial databases is insufficient for any
use with policy implications and that a specific cleanup effort is needed.<br />

Some techniques have been proposed, based on supervised or semi-supervised approaches with clustering 
[@cuxac_efficient_2013]. However, there are few, if any, labeled databases with an open license.<br />
These difficulties have led us, for the French Open Science Monitoring [@jeangirard_monitoring_2019], to build our own
methodology to detect publications with French affiliations.<br />

This document aims at detailing the new methodology for detecting countries in affiliations, and also suggests good
ways to link affiliations to entities listed in international repositories (such as RoR [@noauthor_research_2021],
Grid [@noauthor_grid_2021]) or national ones (in France such as RNSR [@noauthor_rnsr_2021] and Sirene 
[@noauthor_systeme_2021]).<br />

We propose a new approach, using the Elasticsearch search engine, based only on open data, modular and easily adaptable
to other international or local repositories.

# 2. Method

## 2.1 Our matching framework
The problem we are looking for can be summarized as follows: let $q$ be a string, describing an affiliation, and let be 
a set $C$ \{ (condition_i, value_i ) \} (potentially empty) of additional conditions, giving structured information 
about the affiliation described by query. To fix the ideas, we can sometimes know the country of the affiliation. In 
this case, the set $C$ will contain an element : $(country, France)$ for example.<br />

On the other hand, either $R$ a repository of entities (laboratories, institutions, even countries, cities etc). $R$ is
a set of objects with characteristics, such as, for example, in the case of a laboratory, one (or more) name(s),
acronym(s), one (or more) address(es), supervisor(s), etc. The problem of affiliation recognition amounts to finding
the (potentially empty) set of elements of $R$ that correspond to the $q$ and the conditions $C$.<br/>

Let's give an example. With q="French Ministry of Higher Education, Research and Innovation, Paris, France", an empty 
condition set and the grid repository, the expected result is 
[https://grid.ac/institutes/grid.425729.f](https://grid.ac/institutes/grid.425729.f).<br />

This task seems relatively simple to the human mind, but it is actually not so simple to automate. Rather than using a
black-box technique, we propose a simple and modular approach where the user of the algorithm can keep control over the 
risk of error.<br />

There are two types of errors in reality, precision (the proportion of false positives, i.e. how many times the 
algorithm gives a result that is a bad match), and recall (the proportion of false negatives, i.e. how many times the 
algorithm does not give a match when there is a good match).<br />

Let us now introduce two objects: **criterion** and **strategy**.<br />

A **criterion** is a type of element characteristic of the elements of the reference $R$. For example the name or the 
city is a criterion for the grid frame of reference. That is to say that this repository contains information on the 
names (or aliases) and cities of the entities it groups together. To take the previous example, the entity 
grid.425729.f has the following grid_country, grid_name and grid_city criteria (values of these criteria in the grid 
registry):<br />

 - grid_name : 
   - Ministry of Higher Education and Research 
   - Ministère de l’Enseignement Supérieur et de la Recherche 
   - Ministeri d'Educació Superior i Recerca francès
 
- grid_city : 
    - Paris 

 - grid_country : 
    - France

<br/>

A **strategy** is a set of criteria. For example, ['grid_city', 'grid_country', 'grid_name'] is a strategy combining 3 
criteria.<br />

Thus, applying the strategy ['grid_city', 'grid_country', 'grid_name'], amounts to returning all the elements of the
repository $R$ for which there is both a match on the name, the city and on the country with respect to the query
received in input $q$ and $C$. Using the same example, a single match is appropriate, giving the expected results,
with:<br />

  - 'grid_city': ['Ministry of Higher Education, Research and Innovation, **Paris**, France']
  - 'grid_country': ['Higher Education, Research and Innovation, Paris, **France**']
  - 'grid_name': ['French **Ministry** of **Higher** **Education**, **Research** and Innovation, Paris, France']

## 2.2 Criteria and strategies

Depending on the repository $R$ and the nature of the registered objects, many criteria are possible. For example, if a
country repository is handled, criteria can be :<br />

 - the official name and the usual name of the country in different languages and their possible abbreviations (iso 3166
   alpha-2, iso 3166 alpha-3)
 - its subdivisions (regions, provinces...)
 - its cities
 - its institutions, universities, hospitals, etc
 - its rivers, mountains, etc
<br />

In some cases, direct criteria such as these may be insufficient. For example, in the case of a laboratory matching, it 
can happen that the city present in the affiliation signature is not exactly the one indicated in the repository, while 
being geographically very close. To manage this case, we can imagine neighborhood criteria. For example, by establishing
as criteria 'all cities within a radius of x kilometers', or better, by relying on a local geographic reference frame.
In the French case, INSEE has developed in the COG (French Official Geographic Code) [@noauthor_code_2021] several 
divisions, such as urban units or employment zones, which can thus be used as criteria.<br />

The possible strategies are simply all the combinations of the criteria. A risk level can be associated to each
strategy, depending on the risk of false positives.<br />

Thus, in the case of a country matcher, the strategy composed of the only criterion 'name of the country' can be risky.
For example, for an affiliation like "Hotel Dieu de France, Beirut, Lebanon", this strategy would propose two matchings:
France and Lebanon. In this case, France is a false positive. A more demanding strategy, searching for both the country 
name and a city, can avoid this pitfall in this case.<br />

We therefore propose to test several strategies, more or less demanding, starting with the safest (in terms of risk of
false positives). When a strategy has found one or more entries in the repository that meet all its criteria, the
matching is complete.

## 2.3 Implementation with Elasticsearch

Elasticsearch is a very powerful and modular search engine technology. The implementation of our method is done in two
main steps:

 - loading the criteria, each corresponding to an index in elasticsearch
 - the actual matching, by applying a set of strategies.

The choice of strategies to apply is made at the matching level and not at the loading level. The user of the matcher 
can therefore control himself his level of risk of false positives (or in other words his precision / recall balance).
<br />

One feature of elasticsearch is critical for the implementation of our matching method, it is percolation. Usually, 
elasticsearch allows to store documents in an index, and then to perform a query on this index. Percolation allows us 
to do the opposite, i.e. to store queries in an index, and then to search for a document in this query index. Let's
give an example to clarify.<br />

If we take the query "Hotel Dieu de France Beirut Lebanon", we would like to match "Hotel Dieu de France" in the index 
storing the grid_name criteria without "CHU Fort de France" being matched. However, all of them have in common the token 
France. This is possible by using percolation, which will store "Hotel Dieu de France" and "CHU Fort de France" as 
queries.<br />

In addition, these queries can use the diversity offered by elasticsearch. For now, we have implemented queries of type

 - **match_phrase** queries (all terms, consecutively and in the same order) for short criteria where we want an exact 
   match (like city names, or acronyms). 
 - **match** with a *minimum_should_max* parameter at -20%, meaning that at most 20% (rounded down) of the terms can be 
   missing, the order and the consecutive character not being taken into account : for longer criteria like the names 
   of laboratories or supervisors.
<br />

All other implementation details can be read directly in the open source code made available.

### 2.3.1 ES index building

In this part, we will explain more precisely the way we will build the ES indexes to be able to detect different
aspects of the affiliations labels. This will be done against 3 aspects: country, GRID and French Registry RNSR. Those
are only a start but we should be able to add more aspects like ROR, Wikidata, Siren (French institutions
repository), etc.

We here aimed at detecting the country of the affiliation label. As we said before we needed some information about 
existing countries in the world like names, official names, iso 3166 alpha-2 and alpha-3, subdivisions names, 
subdivisions codes. To grab this information we use the python lib [pycountry](https://pypi.org/project/pycountry/). 
This lib gather 249 countries and all the information we needed for each of them. All we will have to do now is to 
create an ES index called `matcher_country_name`, iterate over each country, collect the different names (eg. the name 
of the French country is "France" and its official name is "French Republic") and add each country name in the 
Elasticsearch index as query, remember about the percolate query trix. We will take care to save the iso 3166 alpha-2 
of the dedicated country at the same time.
Once done, I should get this :
```shell
curl -X GET "localhost:9200/matcher_country_name/_search?pretty" 
-H 'Content-Type: application/json' -d'
{
  "query": {
    "percolate": {
      "field": "query",
      "document": {
        "content": "French Ministry of Higher Education, 
        Research and Innovation, Paris, France"
      }
    }
  },          
  "_source": {                    
    "includes": ["country_alpha2"]
  }
}
'
```
The above request will yield the following response:
```shell
{
  "took" : 1,
  "timed_out" : false,
  "_shards" : {
    "total" : 1,
    "successful" : 1,
    "skipped" : 0,
    "failed" : 0
  },
  "hits" : {
    "total" : {
      "value" : 1,
      "relation" : "eq"
    },
    "max_score" : 0.13076457,
    "hits" : [
      {
        "_index" : "matcher_country_name",
        "_type" : "_doc",
        "_id" : "bPUam3oB-wyQTWl-dtqh",
        "_score" : 0.13076457,
        "_source" : {
          "country_alpha2" : [
            "fr"
          ]
        },
        "fields" : {
          "_percolator_document_slot" : [
            0
          ]
        }
      }
    ]
  }
}
```

We do the same with subdivisions names, subdivisions codes and iso 3166 alpha3. We now have 4 indexes:
"matcher_country_name", "matcher_country_subdivision_name", "matcher_country_subdivision_code" and
"matcher_country_alpha3". Each index will represent a criterion of strategy. We could then define a strategy like
["matcher_country_name", "matcher_country_subdivision_name", "matcher_country_alpha3"].

In order to improve performances, we had to do some adjustments with the ES settings and mappings. As default tokenizer,
we use the ICU plugin that has a better support of Unicode. We introduced some Elasticsearch
filters like stop words and stemmer token for both French and English and elisions for French ("l", "q", "jusqu", etc).
We introduced some Elasticsearch analyzers to arrange the previous filters.

Plus we complete the pycountry informations about missing country names like "Vietnam" whose name was only "Viet
Nam" or "Russia" whose name is "Russian Federation".

## 2.4 Evaluation

For a given repository $R$, we fix an ordered list of strategies to apply, allowing us to set up an automatic matching. 
If we have a standard gold (composed of a list of affiliation signatures, and, for each, a list of corresponding 
entities in the $R$ repository), we can apply the matcher on this list, and thus compute the precision and recall of 
the matcher.<br />

We will apply this method in the following section for 3 types of matcher: at the country level, for the grid 
repository and for the French laboratory repository RNSR.

# 3. Results

In order to test our methodology and our strategies, we use a set of 4.705 data. The set of data and the affiliation of 
each data is collected from the Pubmed API. Each data has 5 attributes : affiliation, RNSR, siren, grid, country. The 
affiliation label is a string but it can contain multiple affiliations. The other attributes (rnsr, siren, grid and 
country) are manually collected. This dataset let us compute the precision and recall of each matcher by measuring the 
difference between the expected result and the computed one.

## 3.1 Country detection

For the country matcher, the default strategies are :

['grid_city', 'grid_name', 'grid_acronym', 'country_all_names'],
['grid_city', 'grid_name', 'country_all_names'],
['grid_city', 'grid_acronym', 'country_all_names'],
['grid_city', 'country_all_names'],
['grid_city', 'grid_name', 'country_subdivisions', 'country_alpha3'],
['grid_city', 'grid_name', 'country_alpha3'],
['grid_city', 'grid_acronym', 'country_subdivisions', 'country_alpha3'],
['grid_city', 'country_subdivisions', 'country_alpha3'],
['grid_name', 'country_all_names'],
['country_subdivisions', 'country_all_names'],
['country_all_names'],
['country_subdivisions', 'country_alpha3'],
['grid_name', 'country_subdivisions', 'country_subdivisions_code']

Precision ~= 0.99
Recall ~= 0.93

## 3.2 Grid detection

For the grid matcher, the default strategies are :

['grid_name', 'grid_acronym', 'grid_city', 'grid_country_code'],
['grid_name', 'grid_acronym', 'grid_city', 'grid_country'],
['grid_name', 'grid_city', 'grid_country_code'],
['grid_name', 'grid_city', 'grid_country'],
['grid_acronym', 'grid_city', 'grid_country_code'],
['grid_acronym', 'grid_city', 'grid_country'],
['grid_name', 'grid_country'],
['grid_name', 'grid_country_code'],
['grid_name', 'grid_city']

Precision ~= 0.81
Recall ~= 0.64

## 3.3 French registry RNSR detection

For the RNSR matcher, the default strategies are :

['rnsr_code_number', 'rnsr_supervisor_acronym', 'rnsr_supervisor_name', 'rnsr_zone_emploi'],
['rnsr_code_number', 'rnsr_supervisor_name', 'rnsr_zone_emploi'],
['rnsr_code_number', 'rnsr_acronym'],
['rnsr_code_number', 'rnsr_name'],
['rnsr_code_number', 'rnsr_supervisor_acronym'],
['rnsr_code_number', 'rnsr_supervisor_name'],
['rnsr_code_number', 'rnsr_zone_emploi'],
['rnsr_acronym', 'rnsr_name', 'rnsr_supervisor_name', 'rnsr_zone_emploi'],
['rnsr_acronym', 'rnsr_name', 'rnsr_supervisor_acronym', 'rnsr_zone_emploi'],
['rnsr_acronym', 'rnsr_name', 'rnsr_zone_emploi'],
['rnsr_acronym', 'rnsr_supervisor_acronym', 'rnsr_zone_emploi'],
['rnsr_acronym', 'rnsr_supervisor_name', 'rnsr_zone_emploi'],
['rnsr_name', 'rnsr_supervisor_acronym', 'rnsr_zone_emploi'],
['rnsr_name', 'rnsr_supervisor_name', 'rnsr_zone_emploi'],
['rnsr_name', 'rnsr_acronym', 'rnsr_supervisor_acronym'],
['rnsr_name', 'rnsr_acronym', 'rnsr_supervisor_name'],
['rnsr_name', 'rnsr_zone_emploi'],
['rnsr_acronym', 'rnsr_zone_emploi'],
['rnsr_name', 'rnsr_acronym']

Precision ~= 0.99
Recall ~= 0.80

# 4. Discussion and conclusion

We plan to develop more matchers like RoR and Siren but the methodology will 


## 4.1 Findings

## 4.2 Limitations and future research

# Software and code availability

The source code is released under an MIT license in the GitHub repository 
[https://github.com/dataesr/matcher](https://github.com/dataesr/matcher).

# References
