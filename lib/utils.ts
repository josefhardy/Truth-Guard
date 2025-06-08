import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function validateUrl(url: string): boolean {
  try {
    const urlObj = new URL(url)
    return urlObj.protocol === "http:" || urlObj.protocol === "https:"
  } catch {
    return false
  }
}

export function sanitizeUrl(url: string): string {
  try {
    const urlObj = new URL(url)
    // Remove any potentially dangerous parameters
    urlObj.searchParams.delete("javascript")
    urlObj.searchParams.delete("data")
    return urlObj.toString()
  } catch {
    return url
  }
}

export function extractDomain(url: string): string {
  try {
    const urlObj = new URL(url)
    return urlObj.hostname
  } catch {
    return "Unknown"
  }
}
