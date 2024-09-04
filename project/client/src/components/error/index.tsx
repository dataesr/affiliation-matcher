import { Container, Notice } from "@dataesr/dsfr-plus"

export default function Error({ error }) {
  return (
    <Container style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100px" }}>
      <Notice type="error" closeMode="disallow">
        {error.message}
      </Notice>
    </Container>
  )
}
