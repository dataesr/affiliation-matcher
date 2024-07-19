import { CriterionHighlights, CriteriaHighlights, ResultHighlights } from "./data"

export type CriterionHighlightsArgs = {
  criterion: string
  criterionHighlights: CriterionHighlights
  setTitle: Function
}
export type StrategyHighlightsArgs = {
  strategy: string
  strategyHighlights: CriteriaHighlights
  setTitle: Function
}
export type ResultHighlightsArgs = {
  resultHighlights: ResultHighlights
  setTitle: Function
}
