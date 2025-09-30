import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Combines class names with clsx and merges Tailwind CSS classes
 * @param inputs - Class values to combine and merge
 * @returns Merged class string
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format time duration in seconds to MM:SS format
 * @param seconds - Duration in seconds
 * @returns Formatted time string
 */
export function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

/**
 * Generate a unique ID for transcript entries
 * @returns Unique string ID
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Check if a label indicates toxic/negative content
 * @param label - Sentiment label from Vietnamese STT classification
 * @returns true if content should show warning
 */
export function shouldShowWarning(label: string): boolean {
  return label === 'toxic' || label === 'negative'
}

/**
 * Get display color for sentiment label
 * @param label - Sentiment label
 * @returns Tailwind color class
 */
export function getLabelColor(label: string): string {
  switch (label) {
    case 'toxic':
      return 'bg-red-500'
    case 'negative':
      return 'bg-orange-500'
    case 'positive':
      return 'bg-green-500'
    case 'neutral':
    default:
      return 'bg-gray-500'
  }
}