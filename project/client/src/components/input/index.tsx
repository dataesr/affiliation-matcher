import { Container, SearchBar, Col, Row } from "@dataesr/dsfr-plus"
import useUrl from "../../hooks/useUrl"
import { MATCHERS, matcher_get } from "../../config/matchers"

const YEARS = Array.from({ length: (2011 - 2023) / -1 + 1 }, (_, i) => 2023 + i * -1)

export default function Input() {
  const { currentQuery, currentMatcher, currentYear, handleQueryChange, handleMatcherChange, handleYearChange } = useUrl()
  const enableYear: boolean = matcher_get(currentMatcher)?.year || false
  const placeholder: string = matcher_get(currentMatcher)?.placeholder || "Paris Dauphine University France"

  return (
    <Container className="input">
      <Row gutters className="fr-pb-4w fr-pt-4w fr-mb-2w">
        <Col xs="12" sm="8" lg="8">
          <SearchBar
            key={currentQuery}
            isLarge
            buttonLabel="Match"
            defaultValue={currentQuery}
            placeholder={placeholder}
            onSearch={(value) => handleQueryChange(value.toLowerCase())}
          />
        </Col>
        <Col xs="12" sm="2" lg="2">
          <select
            key={currentMatcher}
            className="fr-select"
            defaultValue={currentMatcher || "DEFAULT"}
            onChange={(matcher) => handleMatcherChange(matcher.target.value)}
          >
            <option key="DEFAULT" value="DEFAULT" disabled>
              Select a matcher
            </option>
            {MATCHERS.map((matcher) => (
              <option key={matcher.key} value={matcher.key}>
                {matcher.label}
              </option>
            ))}
          </select>
        </Col>
        <Col xs="12" sm="2" lg="2">
          <select
            key={currentYear}
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
