const { VITE_API_URL: API_URL, VITE_ELASTIC_URL: ELASTIC_URL } = import.meta.env

export const API_LOAD_URL = `${API_URL}/test_get`
export const API_MATCH_URL = `${API_URL}/match`
export const ES_INDICES_URL = `${ELASTIC_URL}/_cat/indices`
