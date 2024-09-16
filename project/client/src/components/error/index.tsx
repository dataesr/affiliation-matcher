import { Container, Notice } from "@dataesr/dsfr-plus"

export default function Error({ error }: { error: string }) {
  return (
    <Container style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100px" }}>
      <Notice type="error" closeMode="disallow">
        {error}
      </Notice>
    </Container>
  )
}
