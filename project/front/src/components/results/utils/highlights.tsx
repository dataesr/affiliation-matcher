import { MatchHighlights, MatchId, ResultHighlights, TextHighlight } from "../../../types/data"

export const getResultHighlights = (resultsHighlights: MatchHighlights, id: MatchId) =>
  Object.entries(resultsHighlights).reduce((acc: ResultHighlights, [strategy, strategyHighlights]) => {
    Object.entries(strategyHighlights[id]).forEach(([criterion, criterionHiglights]) => {
      if (strategy in acc) acc[strategy][criterion] = criterionHiglights
      else acc[strategy] = { [criterion]: criterionHiglights }
    })
    return acc
  }, {})

export const strategyCriteria = (strategy: string) => strategy.split(";")

const stringFindText = (str: string, text: string): Array<number> =>
  [...str.matchAll(new RegExp(text, "gi"))].map((match) => match.index)

export const getHighlightedText = (highlight: string): TextHighlight => {
  const startTag = "<em>"
  const endTag = "</em>"
  const startTags = stringFindText(highlight, startTag)
  const endTags = stringFindText(highlight, endTag)

  let highlightedArray = []
  let cursor = 0

  for (let i = 0; i < startTags.length; i++) {
    const startIndex = startTags[i]
    const endIndex = endTags[i]

    const highlighted = highlight.slice(startIndex + startTag.length, endIndex)
    highlightedArray.push(highlighted)

    cursor = endIndex + endTag.length
  }

  return highlightedArray
}

export function getHighlightedQuery(highlightedArray: TextHighlight, query: string) {
  let highlightedQuery = query
  highlightedArray.forEach((text) => (highlightedQuery = highlightedQuery.replace(text, `<b>${text}</b>`)))
  return highlightedQuery
}
