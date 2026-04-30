'use client'
import Sidebar from '../../components/layout/Sidebar'
import { useState } from 'react'
import SkillSandbox from '../../components/skills/SkillSandbox'
import GuardrailEditor from '../../components/skills/GuardrailEditor'
import ExecutionLogViewer from '../../components/skills/ExecutionLogViewer'

const TABS = [
  { id: 'registry',   label: 'Registry',    icon: '📋' },
  { id: 'sandbox',    label: 'Sandbox',     icon: '🧪' },
  { id: 'guardrails', label: 'Guardrails',  icon: '🛡️' },
  { id: 'audit',      label: 'Audit Log',   icon: '📊' },
]

// ─── Skill Registry Data ─────────────────────────────────────────────
const SKILLS = [
  // Base Skills (B)
  { id: 'book_appointment', label: 'Book Appointment', type: 'base', status: 'implemented',
    description: 'Book a calendar appointment via external calendar API.', params: ['patient_id', 'appointment_time', 'reason_code'] },
  { id: 'send_communication', label: 'Send Communication', type: 'base', status: 'implemented',
    description: 'Send email/WhatsApp via external messaging provider.', params: ['template_id', 'recipient_address', 'dynamic_vars'] },
  { id: 'ACT_VISION_OCR', label: 'Vision OCR', type: 'base', status: 'implemented',
    description: 'Extract text from clinical images (vitals, lab results).', params: ['image_url', 'extraction_type'] },
  { id: 'KNW_REPORT_SYNTHESIS', label: 'Report Synthesis', type: 'base', status: 'implemented',
    description: 'Aggregate clinical data from multiple sources.', params: ['patient_id', 'data_sources'] },
  { id: 'ACT_CHECKLIST_VERIFY', label: 'Checklist Verify', type: 'base', status: 'implemented',
    description: 'Audit clinical artifacts for presence and completeness.', params: ['patient_id', 'required_documents'] },
  // Functional Skills (F)
  { id: 'SKL_PRE_OP_GATEKEEPER', label: 'Pre-Op Gatekeeper', type: 'functional', status: 'implemented',
    description: 'Multi-step pre-surgery readiness: checklist audit → vitals extraction → verdict.', params: ['patient_id', 'surgery_date', 'required_documents'], composes: ['ACT_CHECKLIST_VERIFY', 'ACT_VISION_OCR'] },
  { id: 'SKL_EXPERT_SYNTHESIS', label: 'Expert Synthesis', type: 'functional', status: 'implemented',
    description: '3-step saga: data aggregation → expert brief formatting → conditional dispatch.', params: ['patient_id', 'data_sources', 'release_approved'], composes: ['KNW_REPORT_SYNTHESIS', 'send_communication'] },
  { id: 'SKL_BASELINE_VIGILANCE', label: 'Baseline Vigilance', type: 'functional', status: 'implemented',
    description: 'Extract vitals via OCR → compare against patient baseline → breach detection.', params: ['patient_id', 'baseline_thresholds', 'image_url'], composes: ['ACT_VISION_OCR'] },
]

export default function SkillsPage() {
  const [activeTab, setActiveTab] = useState('registry')

  const baseSkills = SKILLS.filter(s => s.type === 'base')
  const functionalSkills = SKILLS.filter(s => s.type === 'functional')

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar active="/skills" />
      <main style={{ flex: 1, padding: '32px 36px', overflow: 'auto' }}>

        {/* Header */}
        <div className="fade-up" style={{ marginBottom: 28 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 700 }}>Skills Enablement Pillar</h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
                Base Skills (B) are atomic primitives. Functional Skills (F) orchestrate Base Skills into composite workflows.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <span className="badge badge-blue">{baseSkills.length} Base</span>
              <span className="badge badge-teal">{functionalSkills.length} Functional</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="fade-up" style={{
          display: 'flex', gap: 4, marginBottom: 24,
          borderBottom: '1px solid var(--border)', paddingBottom: 0,
        }}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 18px',
                border: 'none',
                background: activeTab === tab.id ? 'var(--bg-card)' : 'transparent',
                borderBottom: activeTab === tab.id ? '2px solid var(--accent-primary)' : '2px solid transparent',
                color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-muted)',
                fontWeight: activeTab === tab.id ? 700 : 500,
                fontSize: 13, cursor: 'pointer',
                transition: 'all 0.2s',
                borderRadius: '8px 8px 0 0',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              <span>{tab.icon}</span> {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="fade-up">
          {/* Registry Tab */}
          {activeTab === 'registry' && (
            <div>
              {/* Functional Skills */}
              <section style={{ marginBottom: 32 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                  <h2 style={{ fontSize: 15, fontWeight: 600 }}>Functional Skills (F)</h2>
                  <span className="badge badge-teal">Composite Orchestrations</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {functionalSkills.map(skill => (
                    <SkillCard key={skill.id} skill={skill} />
                  ))}
                </div>
              </section>

              {/* Base Skills */}
              <section>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                  <h2 style={{ fontSize: 15, fontWeight: 600 }}>Base Skills (B)</h2>
                  <span className="badge badge-blue">Atomic Primitives</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {baseSkills.map(skill => (
                    <SkillCard key={skill.id} skill={skill} />
                  ))}
                </div>
              </section>
            </div>
          )}

          {/* Sandbox Tab */}
          {activeTab === 'sandbox' && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Skill Sandbox</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  Test skill execution safely with mock wrappers. Select a skill, edit the payload, and execute.
                </p>
              </div>
              <SkillSandbox />
            </div>
          )}

          {/* Guardrails Tab */}
          {activeTab === 'guardrails' && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Guardrail Editor</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  Toggle skills on/off. Disabled skills return 403 — the LLM cannot bypass this gate.
                </p>
              </div>
              <GuardrailEditor />
            </div>
          )}

          {/* Audit Log Tab */}
          {activeTab === 'audit' && (
            <div>
              <div style={{ marginBottom: 16 }}>
                <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Execution Audit Log</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  Full audit trail of every skill execution. Auto-refreshes every 5 seconds. Click to expand details.
                </p>
              </div>
              <ExecutionLogViewer />
            </div>
          )}
        </div>

      </main>
    </div>
  )
}

// ─── Skill Card Component ─────────────────────────────────────────────
function SkillCard({ skill }) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-sm)',
      padding: '16px 20px',
      display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16,
    }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontWeight: 600, fontSize: 14 }}>{skill.label}</span>
          <code style={{
            fontSize: 11, color: 'var(--text-muted)',
            background: 'var(--bg-elevated)', padding: '1px 7px', borderRadius: 4,
          }}>
            {skill.id}
          </code>
          {skill.type === 'functional' && (
            <span className="badge badge-teal" style={{ fontSize: 9 }}>FUNCTIONAL</span>
          )}
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>
          {skill.description}
        </p>
        {/* Composes line for functional skills */}
        {skill.composes && (
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
            Composes: {skill.composes.map((c, i) => (
              <code key={c} style={{ color: 'var(--accent-primary)', background: 'var(--accent-glow)', padding: '1px 6px', borderRadius: 4, marginLeft: i > 0 ? 4 : 0 }}>
                {c}
              </code>
            ))}
          </div>
        )}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {skill.params.map(p => (
            <code key={p} style={{
              fontSize: 10, color: 'var(--accent-primary)',
              background: 'var(--accent-glow)', padding: '1px 7px',
              borderRadius: 4, border: '1px solid rgba(0,119,182,0.12)',
            }}>
              {p}
            </code>
          ))}
        </div>
      </div>
      <span className="badge badge-green" style={{ whiteSpace: 'nowrap' }}>
        ✓ Implemented
      </span>
    </div>
  )
}
