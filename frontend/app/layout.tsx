import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { NLPProvider } from "./context/NLPContext"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Plataforma NLP - Procesamiento de Lenguaje Natural",
  description:
    "Plataforma avanzada para procesamiento de documentos con servicios de NLP: generación de preguntas, resúmenes y traducción.",
  keywords: "NLP, procesamiento de lenguaje natural, traducción, resumen, preguntas",
  authors: [{ name: "NLP Platform Team" }],
  viewport: "width=device-width, initial-scale=1",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es">
      <body className={`${inter.className} bg-gray-50`}>
        <NLPProvider>{children}</NLPProvider>
      </body>
    </html>
  )
}
