import { IntlMessageFormat } from "intl-messageformat"
import { Container, Badge, Text, Row } from "@dataesr/dsfr-plus"
import { CriterionHighlightsArgs, ResultHighlightsArgs, StrategyHighlightsArgs } from "../../../types/functions"
import { getHighlightedText, getHighlightedQuery, strategyCriteria } from "../utils/highlights"
import useUrl from "../../../hooks/useUrl"

function CriterionHighlights({ criterion, criterionHighlights, setTitle }: CriterionHighlightsArgs) {
  const { currentQuery } = useUrl()

  const highlightedData = criterionHighlights.map((criterionHighlight) => {
    const highlightedText = getHighlightedText(criterionHighlight[0])
    return {
      highlightedCriterion: highlightedText.join(" "),
      highlightedQuery: getHighlightedQuery(highlightedText, currentQuery),
    }
  })

  const onEnter = (highlightedQuery: string) =>
    setTitle(new IntlMessageFormat(highlightedQuery).format({ b: (chunks) => <strong>{chunks}</strong> }))
  const onLeave = () => setTitle(currentQuery)

  return (
    <Row>
      <Text>{`${criterion} (${highlightedData.length} match${highlightedData.length > 1 ? "es" : ""}):`}</Text>
      {highlightedData.map((data, index) => (
        <Text
          key={index}
          className="fr-ml-1w fr-mr-1w"
          onMouseEnter={() => onEnter(data.highlightedQuery)}
          onMouseLeave={() => onLeave()}
        >
          <strong>{data.highlightedCriterion}</strong>
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
      {Object.entries(strategyHighlights).map(([criterion, criterionHighlights], index) => (
        <CriterionHighlights
          key={index}
          criterion={criterion}
          criterionHighlights={criterionHighlights}
          setTitle={setTitle}
        />
      ))}
    </Container>
  )
}

export default function ResultHighlights({ resultHighlights, setTitle }: ResultHighlightsArgs) {
  return (
    <Container fluid className="fr-mt-4w">
      {Object.entries(resultHighlights).map(([strategy, criteriaHighlights], index) => (
        <StrategyHighlights key={index} strategy={strategy} strategyHighlights={criteriaHighlights} setTitle={setTitle} />
      ))}
    </Container>
  )
}
