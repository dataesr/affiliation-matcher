import { useCallback, useMemo } from "react"
import { useSearchParams } from "react-router-dom"

export default function useUrl() {
  const [searchParams, setSearchParams] = useSearchParams()
  const currentQuery = searchParams.get("q") || ""
  const currentMatcher = searchParams.get("matcher") || ""

  const handleQueryChange = useCallback(
    (query: string) => {
      searchParams.set("q", query)
      setSearchParams(searchParams)
    },
    [searchParams, setSearchParams]
  )

  const handleMatcherChange = useCallback(
    (matcher: string) => {
      searchParams.set("matcher", matcher)
      setSearchParams(searchParams)
    },
    [searchParams, setSearchParams]
  )

  const values = useMemo(() => {
    return {
      currentQuery,
      currentMatcher,
      handleQueryChange,
      handleMatcherChange,
    }
  }, [currentQuery, currentMatcher, handleQueryChange, handleMatcherChange])

  return values
}
