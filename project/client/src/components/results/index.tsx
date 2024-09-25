import { useEffect, useState } from "react"
import { useIntl } from "react-intl"
import { Container, Text, Badge } from "@dataesr/dsfr-plus"
import { MatchResults } from "../../types"
import Error from "../error"
import Result from "./result"
import Fetching from "../fetching"
import ResultsDebug from "./debug"
import useUrl from "../../hooks/useUrl"
import Info from "../info"
import useMatch from "../../hooks/useMatch"

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
        <ResultsDebug resultsDebug={matchResults?.debug} />
      </Container>
    )

  return (
    <Container fluid>
      <Container className="sticky card">
        <Text size="lead">{currentTitle}</Text>
      </Container>
      <Container className="fr-mt-3w">
        <Text size="md">{intl.formatMessage({ id: "match.count" }, { count: matchIds.length })}</Text>
      </Container>
      <Container fluid className="fr-mt-3w">
        {matchIds.map((id, index) => {
          return <Result key={index} resultData={matchResults} resultId={id} setTitle={setTitle} />
        })}
      </Container>
      <ResultsDebug resultsDebug={matchResults?.debug} />
      {/* <div dangerouslySetInnerHTML={{ __html: matchResults?.logs }} /> */}
    </Container>
  )
}
