import { type NextRequest, NextResponse } from "next/server"
import { extractDomain } from "@/lib/utils"

// Simulate known reliable and unreliable domains for demo purposes
const RELIABLE_DOMAINS = [
  "reuters.com",
  "bbc.com",
  "npr.org",
  "apnews.com",
  "pbs.org",
  "cnn.com",
  "nytimes.com",
  "washingtonpost.com",
  "theguardian.com",
]

const UNRELIABLE_DOMAINS = ["fakenews.com", "conspiracy.net", "clickbait.org", "misleading.info"]

function generateAnalysis(url: string) {
  const domain = extractDomain(url)
  const isReliableDomain = RELIABLE_DOMAINS.some((d) => domain.includes(d))
  const isUnreliableDomain = UNRELIABLE_DOMAINS.some((d) => domain.includes(d))

  // Simulate analysis with some randomness for demo
  const baseReliability = isReliableDomain ? 85 : isUnreliableDomain ? 25 : 60
  const variance = Math.random() * 20 - 10 // ±10 points
  const confidence = Math.max(10, Math.min(95, baseReliability + variance))

  const isReliable = confidence >= 60

  const sourceCredibility = Math.max(10, Math.min(95, confidence + (Math.random() * 10 - 5)))
  const factualAccuracy = Math.max(10, Math.min(95, confidence + (Math.random() * 10 - 5)))
  const biasScore = Math.max(5, Math.min(90, 50 + (Math.random() * 30 - 15)))

  const reasoning = []

  if (isReliableDomain) {
    reasoning.push("Source is from a well-established, credible news organization")
    reasoning.push("Domain has a strong track record of factual reporting")
    reasoning.push("Content structure follows journalistic standards")
  } else if (isUnreliableDomain) {
    reasoning.push("Source domain has been flagged for spreading misinformation")
    reasoning.push("Content shows signs of sensationalism and bias")
    reasoning.push("Lacks proper citations and fact-checking")
  } else {
    reasoning.push("Source credibility is moderate - requires additional verification")
    reasoning.push("Content analysis shows mixed reliability indicators")
    reasoning.push("Recommend cross-referencing with established news sources")
  }

  if (confidence > 80) {
    reasoning.push("High confidence in analysis based on multiple factors")
  } else if (confidence < 40) {
    reasoning.push("Low confidence - multiple red flags detected")
  }

  return {
    isReliable,
    confidence: Math.round(confidence),
    reasoning,
    sourceCredibility: Math.round(sourceCredibility),
    factualAccuracy: Math.round(factualAccuracy),
    biasScore: Math.round(biasScore),
    analysisDetails: {
      domain,
      publishDate: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toLocaleDateString(),
      author: ["John Smith", "Jane Doe", "Alex Johnson", "Sarah Wilson"][Math.floor(Math.random() * 4)],
      wordCount: Math.floor(Math.random() * 2000) + 500,
    },
  }
}

export async function POST(request: NextRequest) {
  try {
    const { url } = await request.json()

    if (!url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 })
    }

    // Validate URL format
    try {
      new URL(url)
    } catch {
      return NextResponse.json({ error: "Invalid URL format" }, { status: 400 })
    }

    // Simulate API processing time
    await new Promise((resolve) => setTimeout(resolve, 1500 + Math.random() * 1000))

    // Simulate occasional API failures for testing error handling
    if (Math.random() < 0.05) {
      // 5% chance of failure
      return NextResponse.json({ error: "Service temporarily unavailable. Please try again." }, { status: 503 })
    }

    const analysis = generateAnalysis(url)

    return NextResponse.json(analysis)
  } catch (error) {
    console.error("API Error:", error)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
