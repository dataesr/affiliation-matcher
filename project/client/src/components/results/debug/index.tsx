import { Container, Badge, BadgeGroup, Accordion } from "@dataesr/dsfr-plus"
import { MatchDebug } from "../../../types"

type ResultsDebugArgs = {
  resultsDebug: MatchDebug
}
export default function ResultsDebug({ resultsDebug }: ResultsDebugArgs) {
  console.log("resultsDebug", resultsDebug)

  if (!resultsDebug) return null

  const criterionMatches = (criterion: string) => resultsDebug.criterion?.[criterion] ?? 0

  return (
    <Accordion className="fr-container fr-mt-3w" title="See more">
      {resultsDebug.strategies.map((strategy, index) => (
        <Container key={index} className="debug-item">
          {strategy.equivalent_strategies.map((equivalent) => (
            <BadgeGroup>
              {equivalent.map((criterion) => {
                const matches: number = criterionMatches(criterion)
                return (
                  <Badge color={matches ? "yellow-moutarde" : null}>{`${criterion}: ${matches} match${
                    matches == 1 ? "" : "es"
                  }`}</Badge>
                )
              })}
            </BadgeGroup>
          ))}
          <Badge color={strategy.matches ? "success" : "error"}>{`${strategy.matches} ${
            strategy.matches == 1 ? "possibility" : "possibilities"
          }`}</Badge>
        </Container>
      ))}
    </Accordion>
  )
}
