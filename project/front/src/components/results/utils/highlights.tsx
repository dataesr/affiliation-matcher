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

    const prefix = highlight.slice(cursor, startIndex)
    if (prefix) {
      highlightedArray.push({ value: prefix, highlight: false })
    }

    const highlighted = highlight.slice(startIndex + startTag.length, endIndex)
    highlightedArray.push({ value: highlighted, highlight: true })

    cursor = endIndex + endTag.length
  }

  const suffix = highlight.slice(endTags.pop() + endTag.length)
  if (suffix) {
    highlightedArray.push({ value: suffix, highlight: false })
  }

  return highlightedArray
}

export function getHighlightedQuery(highlightedArray: TextHighlight, query: string) {
  highlightedArray.forEach((text, index) => {
    if (query.startsWith(text.value)) {
      query = query.slice(text.value.length)
    } else {
      const nextIndex = query.indexOf(highlightedArray[index].value)
      const newText = query.slice(0, nextIndex)
      highlightedArray.splice(index, 0, { value: newText, highlight: false })
      query = query.slice(nextIndex)
    }
  })
  return highlightedArray
}

export function displayHighlightedText(highlightedArray: TextHighlight) {
  const display = (
    <span>{highlightedArray.map((text) => (text.highlight ? <strong>{text.value}</strong> : text.value))}</span>
  )
  return display
}
