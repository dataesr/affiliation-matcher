import { createIntl, RawIntlProvider } from "react-intl"
import { Container } from "@dataesr/dsfr-plus"
import { messages } from "../config/messages"
import Input from "../components/input"
import Results from "../components/results"

function HomePage() {
  return (
    <Container fluid>
      <Input />
      <Results />
    </Container>
  )
}

export default function Home() {
  const intl = createIntl({
    locale: "en",
    messages: messages["en"],
  })

  return (
    <RawIntlProvider value={intl}>
      <HomePage />
    </RawIntlProvider>
  )
}
