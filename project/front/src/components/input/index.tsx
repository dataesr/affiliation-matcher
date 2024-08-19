import { Container, SearchBar, Col, Row } from "@dataesr/dsfr-plus"
import useUrl from "../../hooks/useUrl"

const MATCHER_TYPES = [
  { label: "Country", key: "country", year: false },
  { label: "ROR", key: "ror", year: false },
  { label: "RNSR", key: "rnsr", year: true },
  { label: "grid.ac", key: "grid", year: false },
]

const YEARS = Array.from({ length: (2011 - 2023) / -1 + 1 }, (_, i) => 2023 + i * -1)

export default function Input() {
  const { currentQuery, currentMatcher, currentYear, handleQueryChange, handleMatcherChange, handleYearChange } = useUrl()
  const enableYear: boolean = MATCHER_TYPES.find((matcher) => matcher.key == currentMatcher)?.year || false

  return (
    <Container className="bg-input">
      <Row gutters className="fr-pb-4w fr-pt-4w fr-mb-2w">
        <Col xs="12" sm="8" lg="8">
          <SearchBar
            key={currentQuery}
            isLarge
            buttonLabel="Match"
            defaultValue={currentQuery}
            placeholder="Affiliation string"
            onSearch={(value) => handleQueryChange(value.toLowerCase())}
          />
        </Col>
        <Col xs="12" sm="2" lg="2">
          <select
            className="fr-select"
            defaultValue={currentMatcher || "DEFAULT"}
            onChange={(matcher) => handleMatcherChange(matcher.target.value)}
          >
            <option key="DEFAULT" value="DEFAULT" disabled>
              Select a matcher
            </option>
            {MATCHER_TYPES.map((matcher) => (
              <option key={matcher.key} value={matcher.key}>
                {matcher.label}
              </option>
            ))}
          </select>
        </Col>
        <Col xs="12" sm="2" lg="2">
          <select
            className="fr-select"
            defaultValue={currentYear || "DEFAULT"}
            disabled={!enableYear}
            onChange={(year) => handleYearChange(year.target.value)}
          >
            <option key="DEFAULT" value="DEFAULT" disabled>
              Select a year
            </option>
            {YEARS.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </Col>
      </Row>
    </Container>
  )
}
