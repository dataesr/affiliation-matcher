export type MatchId = string
export type MatchIds = Array<MatchId>

export type MatchEnrichedResult = {
  id: MatchId
  name: Array<string>
  acronym?: Array<string>
  city?: Array<string>
  country?: Array<string>
  paysage_categories?: Array<{ id: string; label?: string; priority?: number }>
}
export type MatchEnrichedResults = Array<MatchEnrichedResult>

export type CriteriaHighlight = Array<Array<string>>
export type CriterionHighlight = Record<string, CriteriaHighlight>
export type StrategyHighlight = Array<string>
export type StrategiesHighlight = Array<StrategyHighlight>
export type MatchHighlight = {
  criterion: CriterionHighlight
  strategies: StrategiesHighlight
}
export type MatchHighlights = Record<MatchId, MatchHighlight>

export type CriterionDebug = Record<string, number>
export type EquivalentStrategiesDebug = {
  criteria: Array<string>
  matches: number
}
export type StrategiesDebug = {
  equivalent_strategies: Array<EquivalentStrategiesDebug>
  possibilities: number
}
export type MatchDebug = {
  criterion: CriterionDebug
  strategies: Array<StrategiesDebug>
}

export type MatchResults = {
  version: string
  index_date: string
  results: MatchIds
  other_ids: MatchIds
  enriched_results: MatchEnrichedResults
  highlights?: MatchHighlights
  debug?: MatchDebug
  logs?: string
}

export type TextHighlight = Array<any>
