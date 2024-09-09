import { useEffect, useState } from "react"
import { Container, Text, Badge } from "@dataesr/dsfr-plus"
import useMatch from "../../hooks/useMatch"
import useUrl from "../../hooks/useUrl"
import Error from "../error"
import Result from "./result"
import Fetching from "../fetching"
import { MatchIds } from "../../types"
import ResultsDebug from "./debug"

export default function Results() {
  const { currentQuery, currentMatcher, currentYear } = useUrl()
  const [currentTitle, setTitle] = useState(currentQuery)
  const { data, isFetching, error } = useMatch(currentQuery, currentMatcher, currentYear)

  useEffect(() => setTitle(currentQuery), [currentQuery])

  if (!currentQuery || !currentMatcher) return null

  if (error) return <Error error={error} />

  if (isFetching) return <Fetching />

  if (!data) return null

  console.log("data", data)

  const matchIds = data.results as MatchIds
  if (!matchIds.length)
    return (
      <>
        <Container className="sticky card">
          <Text size="lead">{currentTitle}</Text>
        </Container>
        <Container className="fr-mt-3w">
          <Badge color="error">{`${currentMatcher} : 0 match`}</Badge>
        </Container>
      </>
    )

  return (
    <Container fluid>
      <Container className="sticky card">
        <Text size="lead">{currentTitle}</Text>
      </Container>
      <Container className="fr-mt-3w">
        <Text size="md">{`${matchIds.length} match${matchIds.length > 1 ? "es" : ""}`}</Text>
      </Container>
      <Container fluid className="fr-mt-3w">
        {matchIds.map((id, index) => {
          return <Result key={index} resultData={data} resultId={id} setTitle={setTitle} />
        })}
      </Container>
      <ResultsDebug resultsDebug={data?.debug} />
    </Container>
  )
}
