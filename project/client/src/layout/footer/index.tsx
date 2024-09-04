import React from "react"
import { Container, Link, Logo } from "@dataesr/dsfr-plus"

export function FooterTop({ children }: { children?: React.ReactNode }) {
  return <div className="fr-footer__top">{children}</div>
}

export function Footer({ children, fluid = false }: { children?: React.ReactNode; fluid?: boolean }) {
  return (
    <footer className="fr-footer fr-mt-3w" role="contentinfo" id="footer">
      <Container fluid={fluid}>{children}</Container>
    </footer>
  )
}

export function FooterBottom({ children, copy }: { children?: React.ReactNode; copy?: React.ReactNode }) {
  const childs = React.Children.toArray(children)
  return (
    <div className="fr-container fr-footer__bottom">
      <ul className="fr-footer__bottom-list">
        {childs.map((child, i) => (
          <li key={i} className="fr-footer__bottom-item">
            {child}
          </li>
        ))}
      </ul>
      {copy ? (
        <div className="fr-footer__bottom-copy">
          <p>{copy}</p>
        </div>
      ) : null}
    </div>
  )
}

export function FooterBody({ children, description }: { children?: React.ReactNode; description?: React.ReactNode }) {
  const links = React.Children.toArray(children).filter((child) => React.isValidElement(child) && child.type === Link)
  const logo = React.Children.toArray(children).filter((child) => React.isValidElement(child) && child.type === Logo)?.[0]

  return (
    <div className="fr-container fr-footer__body">
      {logo ? <div className="fr-footer__brand fr-enlarge-link">{logo}</div> : null}
      <div className="fr-footer__content">
        {description ? <p className="fr-footer__content-desc">{description}</p> : null}
        {links.length ? (
          <ul className="fr-footer__content-list">
            {links.map((link, i) => (
              <li key={i} className="fr-footer__content-item">
                {link}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  )
}
