/**
 * Environment Configuration
 * Centralized environment variable validation and access
 */

export const env = {
  DJANGO_API_URL: process.env.DJANGO_API_URL || '',
  NODE_ENV: process.env.NODE_ENV || 'development',
}

export function validateEnv() {
  const required: string[] = []

  const missing = required.filter(key => !process.env[key])

  if (missing.length > 0) {
    console.warn(`Missing environment variables: ${missing.join(', ')}`)
  }

  return missing.length === 0
}

export function validateAIEnvironment() {
  return {
    hasGrok: !!process.env.GROK_API_KEY,
    hasGroq: !!process.env.GROQ_API_KEY,
    hasLlama: !!process.env.LLAMA_ENDPOINT,
    hasSupabase: false,
  }
}
