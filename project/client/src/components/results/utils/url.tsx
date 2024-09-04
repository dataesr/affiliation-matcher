import { MatchId } from "../../../types/data"

export function getResultUrl(resultId: MatchId, currentMatcher: string) {
  if (currentMatcher === "ror") return `https://ror.org/${resultId}`
  if (currentMatcher === "rnsr")
    return `https://appliweb.dgri.education.fr/rnsr/PresenteStruct.jsp?numNatStruct=${resultId}&PUBLIC=OK`
  if (currentMatcher === "paysage") return `https://paysage.staging.dataesr.ovh/structures/${resultId}`
  return null
}
