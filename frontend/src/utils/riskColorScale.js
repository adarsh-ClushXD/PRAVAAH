/**
 * Utility functions for risk data formatting and color mapping.
 */

export const RISK_COLORS = {
  LOW: { bg: 'rgba(0, 230, 118, 0.85)', text: '#00E676', fill: '#00E676', tailwind: 'risk-low' },
  MODERATE: { bg: 'rgba(255, 184, 0, 0.85)', text: '#FFB800', fill: '#FFB800', tailwind: 'risk-moderate' },
  HIGH: { bg: 'rgba(255, 107, 0, 0.85)', text: '#FF6B00', fill: '#FF6B00', tailwind: 'risk-high' },
  'VERY HIGH': { bg: 'rgba(255, 45, 85, 0.85)', text: '#FF2D55', fill: '#FF2D55', tailwind: 'risk-critical' },
  CRITICAL: { bg: 'rgba(156, 39, 176, 0.85)', text: '#CE93D8', fill: '#9C27B0', tailwind: 'risk-extreme' },
}

export const ALERT_COLORS = {
  GREEN:  { border: '#00E676', bg: 'rgba(0,230,118,0.1)',  text: '#00E676' },
  YELLOW: { border: '#FFB800', bg: 'rgba(255,184,0,0.1)',  text: '#FFB800' },
  ORANGE: { border: '#FF6B00', bg: 'rgba(255,107,0,0.1)',  text: '#FF6B00' },
  RED:    { border: '#FF2D55', bg: 'rgba(255,45,85,0.1)',  text: '#FF2D55' },
  PURPLE: { border: '#9C27B0', bg: 'rgba(156,39,176,0.1)', text: '#CE93D8' },
}

export function getRiskColor(riskCategory) {
  return RISK_COLORS[riskCategory] || RISK_COLORS.MODERATE
}

export function getAlertColors(alertLevel) {
  return ALERT_COLORS[alertLevel] || ALERT_COLORS.YELLOW
}

export function getRiskBadgeClass(riskCategory) {
  const map = {
    LOW: 'risk-low',
    MODERATE: 'risk-mod',
    HIGH: 'risk-high',
    'VERY HIGH': 'risk-critical',
    CRITICAL: 'risk-extreme',
  }
  return map[riskCategory] || 'risk-mod'
}

export function getRiskFillColor(riskScore) {
  if (riskScore === null || riskScore === undefined) return '#1e3556'
  if (riskScore < 20) return '#00E676'
  if (riskScore < 40) return '#FFB800'
  if (riskScore < 60) return '#FF6B00'
  if (riskScore < 80) return '#FF2D55'
  return '#9C27B0'
}

export function getRiskOpacity(riskScore) {
  if (riskScore === null || riskScore === undefined) return 0.15
  return 0.2 + (riskScore / 100) * 0.6
}

export function formatRiskScore(score) {
  if (score === null || score === undefined) return '–'
  return score.toFixed(1)
}

export function formatConfidence(score) {
  if (score === null || score === undefined) return '–'
  return `${Math.round(score * 100)}%`
}

export function formatLargeNumber(n) {
  if (!n) return '–'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return n.toString()
}

export function getTimeAgo(dateStr) {
  if (!dateStr) return 'Never'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}
