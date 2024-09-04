import { Outlet } from "react-router-dom"
import { Container } from "@dataesr/dsfr-plus"
import Header from "./Header"
import MainFooter from "./Footer"
import ScrollToTop from "./scroll-to-top"

export default function Layout() {
  return (
    <>
      <Header />
      <Container as="main" role="main" fluid>
        <Outlet />
      </Container>
      <ScrollToTop />
      <MainFooter />
    </>
  )
}
