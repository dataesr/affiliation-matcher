import { Container, Badge, Text, Row } from "@dataesr/dsfr-plus"
import { CriterionHighlightsArgs, ResultHighlightsArgs, StrategyHighlightsArgs } from "../../../types/functions"
import { displayHighlightedText, getHighlightedText, getHighlightedQuery, strategyCriteria } from "../utils/highlights"
import useUrl from "../../../hooks/useUrl"

function CriterionHighlights({ criterion, criterionHighlights, setTitle }: CriterionHighlightsArgs) {
  const { currentQuery } = useUrl()

  const highlightedData = criterionHighlights.map((criterionHighlight) => {
    const highlightedText = getHighlightedText(criterionHighlight[0])
    const highlightedQuery = getHighlightedQuery(highlightedText, currentQuery)
    return {
      highlightedCriterion: displayHighlightedText(highlightedText.filter((text) => text.highlight || text.value === " ")),
      highlightedQuery: displayHighlightedText(highlightedQuery),
    }
  })

  const onEnter = (highlights: JSX.Element) => setTitle(highlights)
  const onLeave = () => setTitle(currentQuery)

  return (
    <Row>
      <Text>{`${criterion} (${highlightedData.length} match${highlightedData.length > 1 ? "es" : ""}):`}</Text>
      {highlightedData.map((data) => (
        <Text
          className="fr-ml-1w fr-mr-1w"
          onMouseEnter={() => onEnter(data.highlightedQuery)}
          onMouseLeave={() => onLeave()}
        >
          {data.highlightedCriterion}
        </Text>
      ))}
    </Row>
  )
}

function StrategyHighlights({ strategy, strategyHighlights, setTitle }: StrategyHighlightsArgs) {
  const criteria = strategyCriteria(strategy)
  const color = criteria.length === Object.keys(strategyHighlights).length ? "success" : "error"

  return (
    <Container>
      <Badge color={color}>{`Strategy: ${criteria.join(", ")}`}</Badge>
      {Object.entries(strategyHighlights).map(([criterion, criterionHighlights]) => (
        <CriterionHighlights criterion={criterion} criterionHighlights={criterionHighlights} setTitle={setTitle} />
      ))}
    </Container>
  )
}

export default function ResultHighlights({ resultHighlights, setTitle }: ResultHighlightsArgs) {
  return (
    <Container fluid className="fr-mt-4w">
      {Object.entries(resultHighlights).map(([strategy, criteriaHighlights]) => (
        <StrategyHighlights strategy={strategy} strategyHighlights={criteriaHighlights} setTitle={setTitle} />
      ))}
    </Container>
  )
}
