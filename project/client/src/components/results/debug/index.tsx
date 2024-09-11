import { Container, Badge, BadgeGroup, Accordion } from "@dataesr/dsfr-plus"
import { useIntl } from "react-intl"
import { MatchDebug } from "../../../types"

type ResultsDebugArgs = {
  resultsDebug: MatchDebug
}
export default function ResultsDebug({ resultsDebug }: ResultsDebugArgs) {
  const intl = useIntl()
  if (!resultsDebug) return null

  const criterionMatches = (criterion: string) => resultsDebug.criterion?.[criterion] ?? 0

  return (
    <Accordion className="fr-container fr-mt-3w" title={intl.formatMessage({ id: "debug.accordion.title" })}>
      {resultsDebug.strategies.map((strategy, index) => (
        <Container key={index} className="debug-item">
          <Badge size="sm" className="fr-mb-3w" color={strategy.possibilities ? "success" : "error"}>{`Matching ${
            strategy.equivalent_strategies.length
          } strategies : ${intl.formatMessage({ id: "possibility.count" }, { count: strategy.possibilities })}`}</Badge>
          {strategy.equivalent_strategies.map((equivalent) => (
            <Container fluid>
              <BadgeGroup className="fr-mb-2w">
                {equivalent.criteria.map((criterion) => {
                  const matches: number = criterionMatches(criterion)
                  return (
                    <Badge size="sm" color={matches ? "yellow-moutarde" : null}>{`${criterion}: ${intl.formatMessage(
                      { id: "match.count" },
                      { count: matches }
                    )}`}</Badge>
                  )
                })}
                {equivalent.matches > 0 && (
                  <Badge size="sm" color="success">
                    {intl.formatMessage({ id: "match.count" }, { count: equivalent.matches })}
                  </Badge>
                )}
              </BadgeGroup>
            </Container>
          ))}
        </Container>
      ))}
    </Accordion>
  )
}
