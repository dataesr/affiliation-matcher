import { useLocation } from "react-router-dom"
import { Header as HeaderWrapper, Logo, Service, Nav, Link } from "@dataesr/dsfr-plus"

const { VITE_APP_NAME, VITE_HEADER_TAG, VITE_MINISTER_NAME } = import.meta.env

export default function Header() {
  const { pathname } = useLocation()

  return (
    <HeaderWrapper>
      <Logo splitCharacter="|" text={VITE_MINISTER_NAME} />
      <Service name={VITE_APP_NAME} tagline={VITE_HEADER_TAG} />
      <Nav>
        <Link current={pathname === "/"} href="/">
          Home
        </Link>
      </Nav>
    </HeaderWrapper>
  )
}
