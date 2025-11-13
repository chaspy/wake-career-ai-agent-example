import {
  articleDetailSchema,
  articleSummarySchema,
  healthResponseSchema,
  profileResponseSchema,
  profileSchema,
  recommendationResponseSchema,
  type ArticleDetail,
  type ArticleSummary,
  type HealthResponse,
  type Profile,
  type ProfileResponse,
  type RecommendationResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8089'

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const message = await response.text()
    throw new ApiError(response.status, message || 'request failed')
  }
  return response
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`, { signal })
  if (!res.ok) {
    throw new ApiError(res.status, 'health check failed')
  }
  const payload = await res.json()
  return healthResponseSchema.parse(payload)
}

export async function fetchProfile(): Promise<ProfileResponse | null> {
  try {
    const res = await request('/api/profile')
    const payload = await res.json()
    return profileResponseSchema.parse(payload)
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null
    }
    throw error
  }
}

export async function saveProfile(profile: Profile): Promise<ProfileResponse> {
  const payload = profileSchema.parse(profile)
  const res = await request('/api/profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  return profileResponseSchema.parse(data)
}

export async function fetchRecommendations(params: {
  profile?: Profile | null
  query?: string
  top_k?: number
}): Promise<RecommendationResponse> {
  const res = await request('/api/recommendations', {
    method: 'POST',
    body: JSON.stringify({
      profile: params.profile ?? undefined,
      query: params.query ?? undefined,
      top_k: params.top_k ?? 3,
    }),
  })
  const data = await res.json()
  return recommendationResponseSchema.parse(data)
}

export async function listArticles(): Promise<ArticleSummary[]> {
  const res = await request('/api/articles')
  const data = await res.json()
  return articleSummarySchema.array().parse(data)
}

export async function fetchArticle(slug: string): Promise<ArticleDetail> {
  const res = await request(`/api/articles/${slug}`)
  const data = await res.json()
  return articleDetailSchema.parse(data)
}
