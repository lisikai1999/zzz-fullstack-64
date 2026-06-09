import client from './client'
import type { ScoreContent, ScoreListItem, ScoreRead } from '@/types/music'

export async function listScores(): Promise<ScoreListItem[]> {
  const res = await client.get('/scores')
  return res.data
}

export async function getScore(id: number): Promise<ScoreRead> {
  const res = await client.get(`/scores/${id}`)
  return res.data
}

export async function createScore(title: string, composer: string, content: ScoreContent): Promise<ScoreRead> {
  const res = await client.post('/scores', { title, composer, content })
  return res.data
}

export async function updateScore(id: number, data: { title?: string; composer?: string; content?: ScoreContent }): Promise<ScoreRead> {
  const res = await client.put(`/scores/${id}`, data)
  return res.data
}

export async function deleteScore(id: number): Promise<void> {
  await client.delete(`/scores/${id}`)
}

export async function validateScore(id: number): Promise<{ valid: boolean; errors: Record<number, string[]> }> {
  const res = await client.post(`/scores/${id}/validate`)
  return res.data
}

export function getMidiUrl(id: number, opts: { metronome?: boolean; start?: number; end?: number } = {}): string {
  const params = new URLSearchParams()
  if (opts.metronome) params.set('metronome', 'true')
  if (opts.start) params.set('start', String(opts.start))
  if (opts.end) params.set('end', String(opts.end))
  const qs = params.toString()
  return `/api/scores/${id}/midi${qs ? '?' + qs : ''}`
}
