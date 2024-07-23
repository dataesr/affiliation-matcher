import { useEffect, useState } from "react"
import { Container, Text } from "@dataesr/dsfr-plus"
import useMatch from "../../hooks/useMatch"
import useUrl from "../../hooks/useUrl"
import Error from "../error"
import Result from "./result"
import Fetching from "../fetching"
import Home from "../home"
import { MatchIds } from "../../types/data"

export default function Results() {
  const { currentQuery, currentMatcher, currentYear } = useUrl()
  const [currentTitle, setTitle] = useState(currentQuery)
  const { data, isFetching, error } = useMatch(currentQuery, currentMatcher, currentYear)

  useEffect(() => setTitle(currentQuery), [currentQuery])

  if (!currentQuery || !currentMatcher) return <Home />

  if (error) return <Error error={error} />

  if (isFetching) return <Fetching />

  if (!data) return null

  console.log("data", data)

  const matchIds = data.results as MatchIds
  if (!matchIds.length)
    return (
      <Container>
        <Text size="lead">{currentTitle}</Text>
        <Text>NO RESULTS</Text>
      </Container>
    )

  return (
    <Container>
      <Text size="lead">{currentTitle}</Text>
      {matchIds.map((id, index) => {
        return <Result key={index} resultData={data} resultId={id} setTitle={setTitle} />
      })}
    </Container>
  )
}
