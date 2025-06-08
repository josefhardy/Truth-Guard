import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Fake News Detector - Verify Article Authenticity",
  description:
    "Advanced AI-powered tool to detect fake news and verify the authenticity of news articles. Combat misinformation with reliable credibility analysis.",
  keywords: "fake news, fact checking, misinformation, news verification, credibility analysis",
  authors: [{ name: "Fake News Detector Team" }],
  viewport: "width=device-width, initial-scale=1",
  robots: "index, follow",
  openGraph: {
    title: "Fake News Detector - Verify Article Authenticity",
    description: "Advanced AI-powered tool to detect fake news and verify the authenticity of news articles.",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Fake News Detector",
    description: "Verify news article authenticity with AI-powered analysis",
  },
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <main role="main">{children}</main>
      </body>
    </html>
  )
}
