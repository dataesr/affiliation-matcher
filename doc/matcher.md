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

# 2. Method

## 2.1 Our matching framework
The problem we are looking for can be summarized as follows: let $q$ be a string, describing an affiliation, and let be a set $C$ \{ (condition_i, value_i ) \} (potentially empty) of additional conditions, giving structured information about the affiliation described by query. To fix the ideas, we can sometimes know the country of the affiliation. In this case, the set $C$ will contain an element : $("country", "France")$ for example.<br/>
On the other hand, either $R$ a repository of entities (laboratories, institutions, even countries, cities etc). $R$ is a set of objects with characteristics, such as, for example, in the case of a laboratory, one (or more) name, acronyms, one (or more) addresses, supervisors, etc. 
The problem of affiliation recognition amounts to finding the (potentially empty) set of elements of $R$ that correspond to the $q$ and the conditions $C$.
<br/>

Let's give an example. With q="French Ministry of Higher Education, Research and Innovation, Paris, France", an empty condition set and the grid repository, the expected result is https://grid.ac/institutes/grid.425729.f <br/>

This task seems relatively simple to the human mind, but it is actually not so simple to automate. 
Rather than using a black-box technique, we propose a simple and modular approach where the user of the algorithm can keep control over the risk of error.
There are two types of errors in reality, precision (the proportion of false positives, i.e. how many times the algorithm gives a result that is a bad match), and recall (the proportion of false negatives, i.e. how many times the algorithm does not give a match when there is a good match).
<br>
Let us now introduce two objects: criteria and strategies. A criterion is a type of element characteristic of the elements of the reference $R$. For example the name or the city is a criterion for the grid frame of reference. That is to say that this repository contains information on the names (or aliases) and cities of the entities it groups together. To take the previous example, the entity grid.425729.f has the following name and city criteria:
  - grid_name:  
    - Ministry of Higher Education and Research
    - Ministry of Higher Education and Research
    - Ministeri d'Educació Superior i Recerca francès
  - grid_city : 
    - Paris 
  - grid_country : 
    - France
<br/>
A strategy is a set of criteria.
<br/>
Thus, applying the strategy name and country and city, amounts to returning all the elements of the repository $R$ for which there is both a match on the name, on the cityand on the country with respect to the query received in input q and C. Using the same example, a single match is appropriate, giving the expected results, with: 
  - 'grid_city': ['Ministry of Higher Education, Research and Innovation, <b>Paris</b>, France']
  - 'grid_country': ['Higher Education, Research and Innovation, Paris, <b>France</b>']
  - 'grid_name': ['French <b>Ministry</b> of <b>Higher</b> <b>Education</b>, <b>Research</b> and Innovation, Paris, France']

## 2.2 Criteria and strategies

## 2.3 Evaluation

# 3. Results

## 3.1 Country detection

## 3.2 Grid detection

## 3.3 French registry RNSR detection

# 4. Discussion and conclusion

## 4.1 Findings

## 4.2 Limitations and future research

# Software and code availability

The source code is released under an MIT license in the GitHub repository https://github.com/dataesr/matcher

# References
