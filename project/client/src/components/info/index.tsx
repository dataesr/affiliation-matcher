import { Container, Notice } from "@dataesr/dsfr-plus"

export default function Info({ info }: { info: string }) {
  return (
    <Container style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100px" }}>
      <Notice type="info" closeMode="disallow">
        {info}
      </Notice>
    </Container>
  )
}
