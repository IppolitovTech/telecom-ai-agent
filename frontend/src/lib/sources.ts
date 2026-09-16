export function formatDocumentTitle(document: string): string {
  const name = document.replace(/\.[^./]+$/, '')
  return name
    .split(/[-_]/)
    .filter(Boolean)
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(' ')
}
