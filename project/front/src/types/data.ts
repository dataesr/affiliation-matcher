export type MatchId = string
export type MatchIds = Array<MatchId>

export type MatchEnrichedResult = {
  id: MatchId
  acronym: Array<string>
  name: Array<string>
  city: Array<string>
  country: Array<string>
}
export type MatchEnrichedResults = Array<MatchEnrichedResult>

export type CriterionHighlight = Array<string>
export type CriterionHighlights = Array<CriterionHighlight>
export type CriteriaHighlights = Record<string, CriterionHighlights>
export type StrategyHighlights = Record<MatchId, CriteriaHighlights>

export type ResultHighlights = Record<string, CriteriaHighlights>
export type MatchHighlights = Record<string, StrategyHighlights>

export type MatchResults = {
  version: string
  index_date: string
  results: MatchIds
  other_ids: MatchIds
  enriched_results: MatchEnrichedResults
  highlights: MatchHighlights
}

export type TextHighlight = Array<any>
