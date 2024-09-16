import { Container, Spinner } from "@dataesr/dsfr-plus"

export default function Fetching() {
  return (
    <Container style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100px" }}>
      <Spinner />
    </Container>
  )
}
