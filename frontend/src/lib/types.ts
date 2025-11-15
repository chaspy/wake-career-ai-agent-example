import { z } from 'zod'

export const healthResponseSchema = z.object({
  ok: z.boolean(),
  mode: z.enum(['fake', 'live']),
})

export type HealthResponse = z.infer<typeof healthResponseSchema>

export const profileSchema = z.object({
  name: z.string().min(1),
  years: z.number().int().nonnegative(),
  current_role: z.string().min(1),
  target_role: z.string().min(1),
  skills: z.array(z.string()).default([]),
  interests: z.array(z.string()).default([]),
  notes: z
    .string()
    .nullish()
    .transform((value) => (value && value.trim().length > 0 ? value : undefined)),
})

export type Profile = z.infer<typeof profileSchema>

export const profileResponseSchema = profileSchema.extend({
  updated_at: z.string().optional().nullable(),
})

export type ProfileResponse = z.infer<typeof profileResponseSchema>

export const citationSchema = z.object({
  source_url: z.string().url(),
  title: z.string(),
  line: z.number().int().nonnegative().optional(),
})

export const recommendationSchema = z.object({
  id: z.string(),
  title: z.string(),
  url: z.string().url(),
  score: z.number(),
  excerpt: z.string(),
  reasons: z.array(z.string()),
  citations: z.array(citationSchema),
})

export type Recommendation = z.infer<typeof recommendationSchema>

export const recommendationResponseSchema = z.object({
  recommendations: z.array(recommendationSchema),
  mode: z.enum(['fake', 'live']),
})

export type RecommendationResponse = z.infer<typeof recommendationResponseSchema>

export const articleSummarySchema = z.object({
  slug: z.string(),
  title: z.string(),
  source_url: z.string().url(),
  published: z.string().optional().nullable(),
  tags: z.array(z.string()).default([]),
  category: z.string().optional().nullable(),
})

export type ArticleSummary = z.infer<typeof articleSummarySchema>

export const articleDetailSchema = articleSummarySchema.extend({
  body: z.string(),
})

export type ArticleDetail = z.infer<typeof articleDetailSchema>

export const jobSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
  company: z.string().optional().nullable(),
  url: z.string().url(),
  location: z.string().optional().nullable(),
  published_at: z.string().optional().nullable(),
  snippet: z.string().optional().nullable(),
  source: z.string(),
})

export type JobSummary = z.infer<typeof jobSummarySchema>

export const jobSearchResponseSchema = z.object({
  jobs: z.array(jobSummarySchema),
  sources: z.array(z.string()),
  queries: z.array(z.string()).default([]),
})

export type JobSearchResponse = z.infer<typeof jobSearchResponseSchema>
