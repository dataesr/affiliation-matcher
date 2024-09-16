import { Container, Link, Logo } from "@dataesr/dsfr-plus"
import { Footer, FooterTop, FooterBody, FooterBottom } from "./footer/index"
import SwitchTheme from "./switch-theme"

const { VITE_MINISTER_NAME, VITE_APP_DESCRIPTION, VITE_VERSION } = import.meta.env

export default function MainFooter() {
  return (
    <Footer fluid={true}>
      <FooterTop>
        <Container></Container>
      </FooterTop>
      <FooterBody description={VITE_APP_DESCRIPTION}>
        <Logo splitCharacter="|" text={VITE_MINISTER_NAME} />
        <Link
          className="fr-footer__content-link"
          target="_blank"
          rel="noreferrer noopener external"
          title="[À MODIFIER - Intitulé] - nouvelle fenêtre"
          href="https://legifrance.gouv.fr"
        >
          legifrance.gouv.fr
        </Link>
        <Link
          className="fr-footer__content-link"
          target="_blank"
          rel="noreferrer noopener external"
          title="[À MODIFIER - Intitulé] - nouvelle fenêtre"
          href="https://gouvernement.fr"
        >
          gouvernement.fr
        </Link>
        <Link
          className="fr-footer__content-link"
          target="_blank"
          rel="noreferrer noopener external"
          title="[À MODIFIER - Intitulé] - nouvelle fenêtre"
          href="https://service-public.fr"
        >
          service-public.fr
        </Link>
        <Link
          className="fr-footer__content-link"
          target="_blank"
          rel="noreferrer noopener external"
          title="[À MODIFIER - Intitulé] - nouvelle fenêtre"
          href="https://data.gouv.fr"
        >
          data.gouv.fr
        </Link>
      </FooterBody>
      <FooterBottom>
        {/* <button className="fr-footer__bottom-link" data-fr-opened="false">
          Unnamed
        </button> */}
        {/* <button
          className="fr-footer__bottom-link fr-icon-theme-fill fr-btn--icon-left"
          aria-controls="fr-theme-modal"
          data-fr-opened="false"
        >
          Theme
        </button> */}
        <Link
          target="_blank"
          rel="noreferer noopenner"
          className="fr-footer__bottom-link"
          href={`https://github.com/dataesr/affiliation-matcher`}
        >
          {`App version ${VITE_VERSION}`}
        </Link>
      </FooterBottom>
      <SwitchTheme />
    </Footer>
  )
}
