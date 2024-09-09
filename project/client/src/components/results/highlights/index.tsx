import { IntlMessageFormat } from "intl-messageformat"
import { Container, Badge, BadgeGroup } from "@dataesr/dsfr-plus"
import { getHighlightedQuery } from "../utils/highlights"
import useUrl from "../../../hooks/useUrl"
import { MatchHighlight } from "../../../types"

export type ResultHighlightsArgs = {
  resultHighlights: MatchHighlight
  setTitle: Function
}

export default function ResultHighlights({ resultHighlights, setTitle }: ResultHighlightsArgs) {
  const { currentQuery } = useUrl()

  const onEnter = (highlightedQuery: string) =>
    setTitle(
      new IntlMessageFormat(highlightedQuery).format({
        b: (chunks) => <strong key={JSON.stringify(chunks)}>{chunks}</strong>,
      })
    )
  const onLeave = () => setTitle(currentQuery)

  return (
    <Container fluid className="fr-mt-2w">
      {Object.entries(resultHighlights.criterion).map(([criterion, highlights], groupIndex) => (
        <BadgeGroup key={groupIndex}>
          <Badge color="success">{criterion}</Badge>
          {highlights.map((highlight, badgeIndex) => (
            <Badge
              key={badgeIndex}
              onMouseEnter={() => onEnter(getHighlightedQuery(highlight, currentQuery))}
              onMouseLeave={() => onLeave()}
            >
              {highlight?.join(" ")}
            </Badge>
          ))}
        </BadgeGroup>
      ))}
    </Container>
  )
}
