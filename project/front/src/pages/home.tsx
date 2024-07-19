import { Container } from "@dataesr/dsfr-plus"
import Input from "../components/input"
import Results from "../components/results"

export default function Home() {
  return (
    <Container fluid>
      <Input />
      <Results />
    </Container>
  )
}
