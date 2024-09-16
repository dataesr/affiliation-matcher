const modules = import.meta.glob("../locales/*.json", {
  eager: true,
  import: "default",
})
export const messages = Object.keys(modules).reduce((acc, key) => {
  const locale = key.match(/\.\/locales\/(.+)\.json$/)?.[1]
  if (locale) {
    return { ...acc, [locale]: modules[key] }
  }
  return acc
}, {})
