"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  Loader2,
  Shield,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  Info,
  Globe,
  Calendar,
  User,
  FileText,
  TrendingUp,
  Eye,
} from "lucide-react"
import { validateUrl, sanitizeUrl } from "@/lib/utils"

interface DetectionResult {
  isReliable: boolean
  confidence: number
  reasoning: string[]
  sourceCredibility: number
  factualAccuracy: number
  biasScore: number
  analysisDetails: {
    domain: string
    publishDate?: string
    author?: string
    wordCount: number
  }
}

export default function FakeNewsDetector() {
  const [url, setUrl] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<DetectionResult | null>(null)
  const [error, setError] = useState("")
  const [urlError, setUrlError] = useState("")

  const handleUrlChange = (value: string) => {
    setUrl(value)
    setUrlError("")
    setError("")
    setResult(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Reset states
    setError("")
    setUrlError("")
    setResult(null)

    // Validate URL
    if (!url.trim()) {
      setUrlError("Please enter a URL")
      return
    }

    if (!validateUrl(url)) {
      setUrlError("Please enter a valid URL (must start with http:// or https://)")
      return
    }

    setIsLoading(true)

    try {
      const sanitizedUrl = sanitizeUrl(url)

      // THIS IS WHERE YOUR BACKEND CONNECTS
      // Change this URL to your backend endpoint
      const response = await fetch("/api/detect-fake-news", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: sanitizedUrl }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      if (data.error) {
        throw new Error(data.error)
      }

      setResult(data)
    } catch (err) {
      console.error("Detection error:", err)
      setError(
        err instanceof Error
          ? err.message
          : "Failed to analyze the article. Please check your internet connection and try again.",
      )
    } finally {
      setIsLoading(false)
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return "text-green-600"
    if (confidence >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getProgressColor = (confidence: number) => {
    if (confidence >= 80) return "bg-green-500"
    if (confidence >= 60) return "bg-yellow-500"
    return "bg-red-500"
  }

  const getReliabilityBadge = (isReliable: boolean, confidence: number) => {
    if (isReliable) {
      return (
        <Badge variant="default" className="bg-green-100 text-green-800 border-green-200 text-lg px-4 py-2">
          <CheckCircle className="w-5 h-5 mr-2" />
          Likely Reliable
        </Badge>
      )
    } else {
      return (
        <Badge variant="destructive" className="bg-red-100 text-red-800 border-red-200 text-lg px-4 py-2">
          <AlertTriangle className="w-5 h-5 mr-2" />
          Potentially Unreliable
        </Badge>
      )
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-center">
            <Shield className="w-8 h-8 text-blue-600 mr-3" />
            <h1 className="text-2xl font-bold text-gray-900">TruthGuard</h1>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">Detect Fake News with AI</h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Combat misinformation with our advanced AI-powered analysis. Simply paste any news article URL to get
            instant credibility insights, source verification, and detailed fact-checking results.
          </p>
        </div>

        {/* Main Analysis Form */}
        <Card className="mb-8 shadow-xl border-0 bg-white/90 backdrop-blur-sm">
          <CardHeader className="pb-6">
            <CardTitle className="flex items-center text-2xl">
              <Globe className="w-6 h-6 mr-3 text-blue-600" />
              Article Analysis
            </CardTitle>
            <CardDescription className="text-lg">
              Enter the URL of any news article to analyze its credibility and detect potential misinformation.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-3">
                <Label htmlFor="url" className="text-base font-medium">
                  News Article URL
                </Label>
                <div className="flex gap-3">
                  <div className="flex-1">
                    <Input
                      id="url"
                      type="url"
                      placeholder="https://example.com/news-article"
                      value={url}
                      onChange={(e) => handleUrlChange(e.target.value)}
                      className={`h-12 text-lg ${urlError ? "border-red-500 focus:border-red-500" : "border-gray-300"}`}
                      disabled={isLoading}
                      aria-describedby={urlError ? "url-error" : undefined}
                      autoComplete="url"
                    />
                    {urlError && (
                      <p id="url-error" className="text-sm text-red-600 mt-2" role="alert">
                        {urlError}
                      </p>
                    )}
                  </div>
                  <Button
                    type="submit"
                    disabled={isLoading || !url.trim()}
                    className="px-8 h-12 text-lg font-semibold"
                    size="lg"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Eye className="w-5 h-5 mr-2" />
                        Analyze Article
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </form>

            {error && (
              <Alert className="mt-6 border-red-200 bg-red-50">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <AlertDescription className="text-red-800 text-base">{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Loading State */}
        {isLoading && (
          <Card className="mb-8 shadow-lg">
            <CardContent className="py-12">
              <div className="text-center space-y-4">
                <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto" />
                <h3 className="text-xl font-semibold">Analyzing Article...</h3>
                <p className="text-gray-600">Our AI is examining the content, checking sources, and verifying facts.</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results Section */}
        {result && (
          <div className="space-y-8">
            {/* Main Result Card */}
            <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
              <CardHeader className="pb-6">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-2xl">Analysis Results</CardTitle>
                  {getReliabilityBadge(result.isReliable, result.confidence)}
                </div>
              </CardHeader>
              <CardContent className="space-y-8">
                {/* Confidence Score */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-semibold">Overall Confidence Score</span>
                    <span className={`text-3xl font-bold ${getConfidenceColor(result.confidence)}`}>
                      {result.confidence}%
                    </span>
                  </div>
                  <Progress value={result.confidence} className="h-3" />
                  <p className="text-sm text-gray-600">
                    Based on source credibility, content analysis, and fact-checking algorithms
                  </p>
                </div>

                <Separator />

                {/* Detailed Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
                    <TrendingUp className="w-8 h-8 text-blue-600 mx-auto mb-3" />
                    <div className="text-3xl font-bold text-blue-700">{result.sourceCredibility}%</div>
                    <div className="text-sm font-medium text-blue-600">Source Credibility</div>
                    <div className="text-xs text-gray-600 mt-1">Domain reputation & history</div>
                  </div>
                  <div className="text-center p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-xl">
                    <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-3" />
                    <div className="text-3xl font-bold text-green-700">{result.factualAccuracy}%</div>
                    <div className="text-sm font-medium text-green-600">Factual Accuracy</div>
                    <div className="text-xs text-gray-600 mt-1">Content verification score</div>
                  </div>
                  <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
                    <AlertTriangle className="w-8 h-8 text-purple-600 mx-auto mb-3" />
                    <div className="text-3xl font-bold text-purple-700">{result.biasScore}%</div>
                    <div className="text-sm font-medium text-purple-600">Bias Detection</div>
                    <div className="text-xs text-gray-600 mt-1">Political & emotional bias</div>
                  </div>
                </div>

                <Separator />

                {/* Analysis Reasoning */}
                <div className="space-y-4">
                  <h3 className="text-xl font-semibold flex items-center">
                    <Info className="w-5 h-5 mr-2 text-blue-600" />
                    Analysis Reasoning
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-6">
                    <ul className="space-y-3">
                      {result.reasoning.map((reason, index) => (
                        <li key={index} className="flex items-start">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-4 flex-shrink-0" />
                          <span className="text-gray-700 leading-relaxed">{reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Article Details Card */}
            <Card className="shadow-lg border-0 bg-white/90 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-xl flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-gray-600" />
                  Article Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <div className="flex items-center text-sm font-medium text-gray-500">
                      <Globe className="w-4 h-4 mr-2" />
                      Domain
                    </div>
                    <p className="text-lg font-semibold text-gray-900">{result.analysisDetails.domain}</p>
                  </div>

                  {result.analysisDetails.publishDate && (
                    <div className="space-y-2">
                      <div className="flex items-center text-sm font-medium text-gray-500">
                        <Calendar className="w-4 h-4 mr-2" />
                        Published Date
                      </div>
                      <p className="text-lg font-semibold text-gray-900">{result.analysisDetails.publishDate}</p>
                    </div>
                  )}

                  {result.analysisDetails.author && (
                    <div className="space-y-2">
                      <div className="flex items-center text-sm font-medium text-gray-500">
                        <User className="w-4 h-4 mr-2" />
                        Author
                      </div>
                      <p className="text-lg font-semibold text-gray-900">{result.analysisDetails.author}</p>
                    </div>
                  )}

                  <div className="space-y-2">
                    <div className="flex items-center text-sm font-medium text-gray-500">
                      <FileText className="w-4 h-4 mr-2" />
                      Word Count
                    </div>
                    <p className="text-lg font-semibold text-gray-900">
                      {result.analysisDetails.wordCount.toLocaleString()} words
                    </p>
                  </div>
                </div>

                <Separator className="my-6" />

                <div className="flex flex-col sm:flex-row gap-4">
                  <Button variant="outline" asChild className="flex-1">
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center justify-center"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      View Original Article
                    </a>
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setUrl("")
                      setResult(null)
                      setError("")
                    }}
                    className="flex-1"
                  >
                    Analyze Another Article
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Disclaimer */}
            <Alert className="border-amber-200 bg-amber-50">
              <Info className="h-5 w-5 text-amber-600" />
              <AlertDescription className="text-amber-800 text-base">
                <strong>Important Disclaimer:</strong> This analysis is provided for informational purposes only. Always
                verify information through multiple reliable sources and use critical thinking when consuming news
                content. No automated system is 100% accurate.
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Features Section */}
        {!result && !isLoading && (
          <div className="mt-16">
            <h3 className="text-3xl font-bold text-center text-gray-900 mb-12">How TruthGuard Works</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center p-6">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Globe className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="text-xl font-semibold mb-3">Source Analysis</h4>
                <p className="text-gray-600">
                  We analyze the credibility and reputation of news sources using comprehensive databases and historical
                  accuracy records.
                </p>
              </div>
              <div className="text-center p-6">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
                <h4 className="text-xl font-semibold mb-3">Content Verification</h4>
                <p className="text-gray-600">
                  Advanced AI algorithms examine article content for factual accuracy, bias detection, and
                  misinformation patterns.
                </p>
              </div>
              <div className="text-center p-6">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="w-8 h-8 text-purple-600" />
                </div>
                <h4 className="text-xl font-semibold mb-3">Real-time Results</h4>
                <p className="text-gray-600">
                  Get instant, detailed analysis with confidence scores and actionable insights to help you make
                  informed decisions.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-white mt-20">
        <div className="max-w-6xl mx-auto px-4 py-12">
          <div className="text-center">
            <div className="flex items-center justify-center mb-4">
              <Shield className="w-8 h-8 text-blue-400 mr-3" />
              <h3 className="text-2xl font-bold">TruthGuard</h3>
            </div>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Empowering informed decision-making through AI-powered fact-checking and news verification.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
