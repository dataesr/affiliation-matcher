import { Container, Badge, BadgeGroup, Accordion } from "@dataesr/dsfr-plus"
import { MatchDebug } from "../../../types"

type ResultsDebugArgs = {
  resultsDebug: MatchDebug
}
export default function ResultsDebug({ resultsDebug }: ResultsDebugArgs) {
  if (!resultsDebug) return null

  const criterionMatches = (criterion: string) => resultsDebug.criterion?.[criterion] ?? 0

  return (
    <Accordion className="fr-container fr-mt-3w" title="See more">
      {resultsDebug.strategies.map((strategy, index) => (
        <Container key={index} className="debug-item">
          <Badge className="fr-mb-3w" color={strategy.possibilities ? "success" : "error"}>{`Matching ${
            strategy.equivalent_strategies.length
          } strategies : ${strategy.possibilities} ${strategy.possibilities == 1 ? "possibility" : "possibilities"}`}</Badge>
          {strategy.equivalent_strategies.map((equivalent) => (
            <Container fluid>
              <BadgeGroup className="fr-mb-2w">
                {equivalent.criteria.map((criterion) => {
                  const matches: number = criterionMatches(criterion)
                  return (
                    <Badge color={matches ? "yellow-moutarde" : null}>{`${criterion}: ${matches} match${
                      matches == 1 ? "" : "es"
                    }`}</Badge>
                  )
                })}
                {equivalent.matches > 0 && (
                  <Badge color="success">{`${equivalent.matches} match${equivalent.matches == 1 ? "" : "es"}`}</Badge>
                )}
              </BadgeGroup>
            </Container>
          ))}
        </Container>
      ))}
    </Accordion>
  )
}
