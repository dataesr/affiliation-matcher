import { TextHighlight } from "../../../types"

export function getHighlightedQuery(highlightedArray: TextHighlight, query: string) {
  let highlightedQuery = query
  highlightedArray.forEach((text) => (highlightedQuery = highlightedQuery.replace(text, `<b>${text}</b>`)))
  highlightedQuery = highlightedQuery.replace(/'/g, "''")
  return highlightedQuery
}
