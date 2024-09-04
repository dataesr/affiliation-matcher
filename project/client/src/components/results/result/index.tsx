import { Container, Badge, Row, BadgeGroup, Accordion } from "@dataesr/dsfr-plus"
import { MatchId, MatchResults } from "../../../types/data"
import useUrl from "../../../hooks/useUrl"
import { getResultHighlights } from "../utils/highlights"
import { getResultUrl } from "../utils/url"
import ResultHighlights from "../highlights"

export default function Result({
  resultData,
  resultId,
  setTitle,
}: {
  resultData: MatchResults
  resultId: MatchId
  setTitle: Function
}) {
  const { currentMatcher } = useUrl()

  const { results: resultsIds, enriched_results: resultsEnriched, highlights: resultsHighlights } = resultData
  const resultIndex = resultsIds.findIndex((element) => element === resultId)
  const resultEnriched = resultsEnriched[resultIndex]
  const resultHighlights = getResultHighlights(resultsHighlights, resultId)
  const resultUrl = getResultUrl(resultId, currentMatcher)

  return (
    <Container className="card fr-mt-2w">
      <Row>
        <BadgeGroup className="fr-mt-2w">
          {resultUrl ? (
            <Badge
              as="a"
              href={resultUrl}
              target="_blank"
              color="yellow-moutarde"
            >{`${currentMatcher} : ${resultId}`}</Badge>
          ) : (
            <Badge color="yellow-moutarde">{`${currentMatcher} : ${resultId}`}</Badge>
          )}
          {resultEnriched?.acronym?.length && <Badge color="green-archipel">{resultEnriched.acronym[0]}</Badge>}
          {resultEnriched?.name?.length && <Badge color="blue-ecume">{resultEnriched.name[0]}</Badge>}
          {resultEnriched?.city?.length && <Badge color="purple-glycine">{resultEnriched.city[0]}</Badge>}
          {resultEnriched?.country?.length && <Badge color="pink-macaron">{resultEnriched.country[0]}</Badge>}
        </BadgeGroup>
      </Row>
      <Accordion title="Highlights">
        <ResultHighlights resultHighlights={resultHighlights} setTitle={setTitle} />
      </Accordion>
    </Container>
  )
}
