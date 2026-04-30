'use client'
import Sidebar from '../components/layout/Sidebar'
import { useState, useEffect } from 'react'
import {
  KnowledgeIcon,
  BrainIcon,
  PersonaIcon,
  WarningIcon
} from '../components/ui/SparkleIcons'

const PIPELINE_STAGES = [
  { name: 'Document Ingestion', status: 'built', module: 'knowledge_hub' },
  { name: 'Universal Structure Builder', status: 'built', module: 'knowledge_hub' },
  { name: 'Embedding + RAG Index', status: 'built', module: 'knowledge_hub' },
  { name: 'Divergence Scanner', status: 'built', module: 'knowledge_hub' },
  { name: 'Master Case Generation', status: 'partial', module: 'knowledge_hub' },
  { name: 'Continuous Loop', status: 'partial', module: 'knowledge_hub' },
  { name: 'KB → Persona Bridge', status: 'in_progress', module: 'integration' },
  { name: 'AI Journalist Extraction', status: 'built', module: 'expert_persona' },
  { name: 'Persona Manifestation', status: 'built', module: 'expert_persona' },
  { name: 'Shadow Mode Review', status: 'built', module: 'expert_persona' },
  { name: 'Skills Layer', status: 'built', module: 'skills' },
  { name: 'Runtime Retrieval + Chat', status: 'planned', module: 'retrieval' },
]

const STATUS_STYLE = {
  built: { bg: '#CAF0F8', color: '#03045E', border: '#90E0EF', label: 'Built' },
  partial: { bg: '#FFFBEB', color: '#D97706', border: '#FDE68A', label: 'Partial' },
  in_progress: { bg: '#EFF6FF', color: '#3B82F6', border: '#BFDBFE', label: 'In Progress' },
  planned: { bg: '#F9FAFB', color: '#9CA3AF', border: '#E5E7EB', label: 'Planned' },
}

const MODULE_COLORS = {
  knowledge_hub: '#0077B6',
  expert_persona: '#03045E',
  integration: '#F59E0B',
  skills: '#00B4D8',
  retrieval: '#90E0EF',
}

export default function DashboardPage() {
  const [health, setHealth] = useState(null)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(r => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: 'offline' }))

    fetch('/api/stats?expertId=demo')
      .then(r => r.json())
      .then(setStats)
      .catch(() => setStats(null))
  }, [])

  const statCards = [
    { label: 'Documents Ingested', value: stats?.documentsIngested ?? '—', color: '#0077B6', bg: '#CAF0F8', border: '#90E0EF', icon: <KnowledgeIcon size={22} /> },
    { label: 'Master Cases', value: stats?.masterCases ?? '—', color: '#03045E', bg: '#CAF0F8', border: '#90E0EF', icon: <BrainIcon size={22} /> },
    { label: 'Persona Manifests', value: stats?.personaManifests ?? '—', color: '#00B4D8', bg: '#CAF0F8', border: '#90E0EF', icon: <PersonaIcon size={22} /> },
    { label: 'Knowledge Gaps Flagged', value: stats?.knowledgeGapsFlagged ?? '—', color: '#EF4444', bg: '#FEF2F2', border: '#FECACA', icon: <WarningIcon size={22} /> },
  ]

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#F4F7FB' }}>
      <Sidebar active="/" />

      <main style={{ flex: 1, padding: '32px 36px', overflow: 'auto' }}>

        {/* Header */}
        <div className="fade-up" style={{ marginBottom: 36 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{ fontSize: 26, fontWeight: 700, marginBottom: 4, color: '#03045E' }}>Doctor Digital Twin</h1>
              <p style={{ color: '#475569', fontSize: 14 }}>
                Fertility Specialist · Knowledge Hub + Persona Engine · Season 1
              </p>
            </div>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 16px',
              borderRadius: '12px',
              border: `1px solid ${health?.status === 'healthy' ? '#90E0EF' : '#FECACA'}`,
              background: health?.status === 'healthy' ? '#CAF0F8' : '#FEF2F2',
              fontSize: 13,
              color: health?.status === 'healthy' ? '#03045E' : '#DC2626',
              fontWeight: 500,
            }}>
              <span style={{
                width: 7, height: 7, borderRadius: '50%',
                background: health?.status === 'healthy' ? '#0077B6' : '#EF4444',
                display: 'inline-block',
              }} />
              {health?.status === 'healthy' ? `Backend online · ${health.active_domain}` : 'Backend offline'}
            </div>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="fade-up" style={{
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32
        }}>
          {statCards.map((card, i) => (
            <div key={i} style={{
              background: '#FFFFFF',
              border: '1px solid #E2E8F0',
              borderRadius: '12px',
              padding: '22px 24px',
              position: 'relative',
              overflow: 'hidden',
              transition: 'all 0.2s',
              boxShadow: '0 4px 12px rgba(3, 4, 94, 0.03)',
            }}>
              <div style={{
                width: 44, height: 44, borderRadius: '8px',
                background: card.bg, border: `1px solid ${card.border}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: 14,
              }}>{card.icon}</div>
              <div style={{ fontSize: 30, fontWeight: 800, color: card.color, lineHeight: 1 }}>
                {card.value}
              </div>
              <div style={{ fontSize: 13, color: '#475569', marginTop: 6, fontWeight: 500 }}>
                {card.label}
              </div>
            </div>
          ))}
        </div>

        {/* Pipeline Status */}
        <div className="fade-up" style={{
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: '16px',
          padding: '28px 30px',
          boxShadow: '0 4px 12px rgba(3, 4, 94, 0.03)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, color: '#03045E' }}>Pipeline Status</h2>
            <span style={{ background: '#CAF0F8', color: '#03045E', padding: '4px 12px', borderRadius: 99, fontSize: 12, fontWeight: 700 }}>12 STAGES</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            {PIPELINE_STAGES.map((stage, i) => {
              const style = STATUS_STYLE[stage.status]
              return (
                <div key={i} style={{
                  padding: '16px 20px',
                  borderRadius: '12px',
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <div>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: '#03045E', marginBottom: 4 }}>{stage.name}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: MODULE_COLORS[stage.module] }} />
                      <span style={{ fontSize: 11, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>{stage.module.replace('_', ' ')}</span>
                    </div>
                  </div>
                  <span style={{
                    padding: '4px 10px',
                    borderRadius: '99px',
                    fontSize: 11,
                    fontWeight: 700,
                    background: style.bg,
                    color: style.color,
                    border: `1px solid ${style.border}`,
                    textTransform: 'uppercase'
                  }}>{style.label}</span>
                </div>
              )
            })}
          </div>
        </div>

      </main>
    </div>
  )
}
