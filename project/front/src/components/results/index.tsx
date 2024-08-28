import { useEffect, useState } from "react"
import { Container, Text, Badge } from "@dataesr/dsfr-plus"
import useMatch from "../../hooks/useMatch"
import useUrl from "../../hooks/useUrl"
import Error from "../error"
import Result from "./result"
import Fetching from "../fetching"
import { MatchIds } from "../../types/data"

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
      <Container>
        <Text size="lead">{currentTitle}</Text>
        <Badge color="error">{`${currentMatcher} : no results`}</Badge>
      </Container>
    )

  return (
    <Container fluid>
      <Container className="sticky">
        <Text size="lead">{currentTitle}</Text>
      </Container>
      <Container fluid className="fr-mt-5w">
        {matchIds.map((id, index) => {
          return <Result key={index} resultData={data} resultId={id} setTitle={setTitle} />
        })}
      </Container>
    </Container>
  )
}
