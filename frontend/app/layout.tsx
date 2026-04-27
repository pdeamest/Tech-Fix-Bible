import "./globals.css";

export const metadata = {
  title: 'Tech-Fix-Bible',
  description: 'Bilingual technical KB with GIN-indexed search and error-code analytics',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
