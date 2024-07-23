import { Container, SearchBar, Col, Row } from "@dataesr/dsfr-plus"
import useUrl from "../../hooks/useUrl"

const MATCHER_TYPES = [
  { label: "Country", key: "country" },
  { label: "ROR", key: "ror" },
  { label: "RNSR", key: "rnsr" },
  { label: "Paysage", key: "paysage" },
]

export default function Input() {
  const { currentQuery, currentMatcher, handleQueryChange, handleMatcherChange } = useUrl()

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
            onSearch={(value) => handleQueryChange(value)}
          />
        </Col>
        <Col xs="12" sm="4" lg="4">
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
      </Row>
    </Container>
  )
}
