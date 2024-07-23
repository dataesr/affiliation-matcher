import { useCallback, useMemo } from "react"
import { useSearchParams } from "react-router-dom"

export default function useUrl() {
  const [searchParams, setSearchParams] = useSearchParams()
  const currentQuery = searchParams.get("q") || ""
  const currentMatcher = searchParams.get("matcher") || ""
  const currentYear = searchParams.get("year") || ""

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
      searchParams.delete("year")
      setSearchParams(searchParams)
    },
    [searchParams, setSearchParams]
  )

  const handleYearChange = useCallback(
    (year: string) => {
      searchParams.set("year", year)
      setSearchParams(searchParams)
    },
    [searchParams, setSearchParams]
  )

  const values = useMemo(() => {
    return {
      currentQuery,
      currentMatcher,
      currentYear,
      handleQueryChange,
      handleMatcherChange,
      handleYearChange,
    }
  }, [currentQuery, currentMatcher, currentYear, handleQueryChange, handleMatcherChange, handleYearChange])

  return values
}
