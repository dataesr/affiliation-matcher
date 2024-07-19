import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"
import { API_MATCH_URL } from "../config/api"

const fetchMatch = async (query: string, matcher: string) => {
  const body = { type: matcher, query: query }

  const response = await fetch(API_MATCH_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  if (!response.ok) throw new Error(`API error: ${response.status}`)
  const data = await response.json()
  return data
}

export default function useMatch(query: string, matcher: string) {
  const { data, error, isFetching } = useQuery({
    queryKey: ["match", query, matcher],
    queryFn: () => fetchMatch(query, matcher),
    staleTime: 1000 * 60 * 5,
  })

  const values = useMemo(() => {
    return { data, isFetching, error }
  }, [data, isFetching, error])

  return values
}
