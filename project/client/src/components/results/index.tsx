import { useEffect, useState } from "react"
import { useIntl } from "react-intl"
import { Container, Text, Badge } from "@dataesr/dsfr-plus"
import { MatchIds, MatchResults } from "../../types"
import Error from "../error"
import Result from "./result"
import Fetching from "../fetching"
import ResultsDebug from "./debug"
import useUrl from "../../hooks/useUrl"
import Info from "../info"
import useMatch from "../../hooks/useMatch"

type MatcherResultsArgs = {
  matchIds: MatchIds
  matchResults: MatchResults
  setTitle: any
}

function MatcherResults({ matchIds, matchResults, setTitle }: MatcherResultsArgs) {
  const intl = useIntl()
  return (
    <Container fluid>
      <Container className="fr-mt-3w">
        <Text size="md">{intl.formatMessage({ id: "match.count" }, { count: matchIds.length })}</Text>
      </Container>
      <Container fluid className="fr-mt-3w">
        {matchIds.map((id, index) => {
          return <Result key={index} resultData={matchResults} resultId={id} setTitle={setTitle} />
        })}
      </Container>
    </Container>
  )
}

function PaysageResults({ matchIds, matchResults, setTitle }: MatcherResultsArgs) {
  const intl = useIntl()

  const DEFAULT_CATEGORY = "Others"
  const DEFAULT_PRIORITY = 99

  const categories = matchResults?.enriched_results?.reduce((acc, res) => {
    if (res?.paysage_categories) {
      const lowestPriority = Math.min(...res.paysage_categories.map((category) => category?.priority || DEFAULT_PRIORITY))
      res.paysage_categories
        .filter((category) => (category?.priority || DEFAULT_PRIORITY) === lowestPriority)
        .forEach((category) => {
          const label = category?.label || DEFAULT_CATEGORY
          const priority = category?.priority || DEFAULT_PRIORITY
          acc[label] = acc?.[label]
            ? { ...acc[label], ids: [...acc[label].ids, res.id] }
            : { ids: [res.id], priority: priority }
        })
    } else {
      acc[DEFAULT_CATEGORY] = acc?.[DEFAULT_CATEGORY]
        ? { ...acc[DEFAULT_CATEGORY], ids: [...acc[DEFAULT_CATEGORY].ids, res.id] }
        : { ids: [res.id], priority: DEFAULT_PRIORITY }
    }
    return acc
  }, {} as Record<string, { ids: MatchIds; priority: number }>)

  if (!categories || (Object.keys(categories)?.length === 1 && Object.keys(categories)[0] === DEFAULT_CATEGORY))
    return <MatcherResults matchIds={matchIds} matchResults={matchResults} setTitle={setTitle} />

  return (
    <Container fluid>
      {Object.entries(categories)
        .sort((a, b) => a[1].priority - b[1].priority)
        .map(([key, values]) => (
          <Container fluid>
            <Container className="fr-mt-3w">
              <Text size="md">
                {key}
                {" : "}
                {intl.formatMessage({ id: "match.count" }, { count: values.ids.length })}
              </Text>
            </Container>
            <Container fluid className="fr-mt-3w">
              {values.ids.map((id, index) => {
                return <Result key={index} resultData={matchResults} resultId={id} setTitle={setTitle} />
              })}
            </Container>
          </Container>
        ))}
    </Container>
  )
}

export default function Results() {
  const intl = useIntl()
  const { currentQuery, currentMatcher, currentYear } = useUrl()
  const { data, isFetching, error } = useMatch(currentQuery, currentMatcher, currentYear)
  const [currentTitle, setTitle] = useState(currentQuery)

  useEffect(() => setTitle(currentQuery), [currentQuery])

  console.log("data", data)

  if (currentQuery === null && currentMatcher === null) return null
  if (!currentQuery) return <Info info={intl.formatMessage({ id: "info.missing.query" })} />
  if (!currentMatcher) return <Info info={intl.formatMessage({ id: "info.missing.matcher" })} />

  if (isFetching) return <Fetching />

  if (error) return <Error error={error?.message} />
  if (!data) return <Error error="No data" />
  if (!data?.results) return <Error error={data?.Error} />

  const matchResults: MatchResults = data
  const matchIds = matchResults.results

  if (!matchIds.length)
    return (
      <Container fluid>
        <Container className="sticky card">
          <Text size="lead">{currentTitle}</Text>
        </Container>
        <Container className="fr-mt-3w">
          <Badge color="error">{`${currentMatcher} : ${intl.formatMessage({ id: "match.count" }, { count: 0 })}`}</Badge>
        </Container>
        <ResultsDebug resultsDebug={matchResults?.debug} resultsLogs={matchResults?.logs} />
      </Container>
    )

  return (
    <Container fluid>
      <Container className="sticky card">
        <Text size="lead">{currentTitle}</Text>
      </Container>
      {currentMatcher === "paysage" ? (
        <PaysageResults matchIds={matchIds} matchResults={matchResults} setTitle={setTitle} />
      ) : (
        <MatcherResults matchIds={matchIds} matchResults={matchResults} setTitle={setTitle} />
      )}
      <ResultsDebug resultsDebug={matchResults?.debug} resultsLogs={matchResults?.logs} />
    </Container>
  )
}
