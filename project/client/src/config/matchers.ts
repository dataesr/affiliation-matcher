export const MATCHERS = [
  {
    label: "Country",
    key: "country",
    year: false,
    placeholder: "Department of Medical Genetics, Hotel Dieu de France, Beirut, Lebanon",
  },
  { label: "ROR", key: "ror", year: false, placeholder: "Paris Dauphine University France" },
  { label: "RNSR", key: "rnsr", year: true, placeholder: "IPAG Institut de Planétologie et d'Astrophysique de Grenoble" },
  { label: "grid.ac", key: "grid", year: false, placeholder: "Paris Dauphine University France" },
  { label: "Paysage", key: "paysage", year: true, placeholder: "UTC Université de Technologie de Compiègne" },
]

export const matcher_get = (key: string) => MATCHERS.find((matcher) => matcher.key == key)
