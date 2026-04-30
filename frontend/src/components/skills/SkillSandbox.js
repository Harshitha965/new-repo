'use client'
import { useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

const DEFAULT_PAYLOADS = {
  book_appointment: '{\n  "patient_id": "123e4567-e89b-12d3-a456-426614174000",\n  "appointment_time": "2026-12-01T10:00:00Z",\n  "reason_code": "CONSULT"\n}',
  send_communication: '{\n  "template_id": "welcome_01",\n  "recipient_address": "patient@example.com",\n  "dynamic_vars": {}\n}',
  SKL_PRE_OP_GATEKEEPER: '{\n  "patient_id": "123e4567-e89b-12d3-a456-426614174000",\n  "surgery_date": "2026-12-05T08:00:00Z",\n  "required_documents": [\n    "Surgical Consent Form",\n    "Anesthesia Clearance"\n  ]\n}',
  SKL_EXPERT_SYNTHESIS: '{\n  "patient_id": "123e4567-e89b-12d3-a456-426614174000",\n  "data_sources": [\n    "lab_panel_001",\n    "vitals_snapshot_002"\n  ],\n  "release_approved": false\n}',
  SKL_BASELINE_VIGILANCE: '{\n  "patient_id": "123e4567-e89b-12d3-a456-426614174000",\n  "baseline_thresholds": {\n    "bp_systolic": [100, 140],\n    "bp_diastolic": [60, 90],\n    "hr": [60, 100]\n  }\n}'
}

export default function SkillSandbox() {
  const [skillName, setSkillName] = useState('book_appointment')
  const [payloadStr, setPayloadStr] = useState(DEFAULT_PAYLOADS.book_appointment)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSkillChange = (e) => {
    const val = e.target.value
    setSkillName(val)
    if (DEFAULT_PAYLOADS[val]) {
      setPayloadStr(DEFAULT_PAYLOADS[val])
    }
  }

  const handleExecute = async () => {
    setLoading(true)
    setResult(null)
    try {
      const payloadObj = JSON.parse(payloadStr)
      const reqBody = {
        skill_name: skillName,
        payload: payloadObj,
        metadata: {
          workflow_id: "00000000-0000-0000-0000-000000000000",
          expert_id: "11111111-1111-1111-1111-111111111111"
        }
      }

      const res = await fetch(`${API_BASE}/skills/execute/${skillName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reqBody)
      })
      
      const data = await res.json()
      setResult({ status: res.status, data })
    } catch (err) {
      setResult({ status: 'Error', data: err.toString() })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)',
        padding: '24px',
        marginBottom: 16,
      }}>
        <div style={{ marginBottom: 20 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
            Select Skill
          </label>
          <select
            value={skillName}
            onChange={handleSkillChange}
            style={{
              width: '100%', padding: '10px 12px', borderRadius: 8,
              border: '1px solid var(--border)', background: 'var(--bg-elevated)',
              color: 'var(--text-primary)', fontSize: 13, fontWeight: 500,
            }}
          >
            <optgroup label="Base Skills (B)">
              <option value="book_appointment">book_appointment</option>
              <option value="send_communication">send_communication</option>
            </optgroup>
            <optgroup label="Functional Skills (F)">
              <option value="SKL_PRE_OP_GATEKEEPER">SKL_PRE_OP_GATEKEEPER</option>
              <option value="SKL_EXPERT_SYNTHESIS">SKL_EXPERT_SYNTHESIS</option>
              <option value="SKL_BASELINE_VIGILANCE">SKL_BASELINE_VIGILANCE</option>
            </optgroup>
          </select>
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
            JSON Payload
          </label>
          <textarea
            value={payloadStr}
            onChange={e => setPayloadStr(e.target.value)}
            style={{
              width: '100%', minHeight: 180, padding: '12px',
              borderRadius: 8, border: '1px solid var(--border)',
              background: 'var(--bg-elevated)', color: 'var(--text-primary)',
              fontFamily: 'monospace', fontSize: 12, resize: 'vertical',
              lineHeight: 1.6,
            }}
          />
        </div>

        <button
          onClick={handleExecute}
          disabled={loading}
          style={{
            background: 'linear-gradient(135deg, #0077B6 0%, #00B4D8 100%)',
            color: '#fff', border: 'none', padding: '10px 24px',
            borderRadius: 8, fontWeight: 700, fontSize: 13,
            cursor: loading ? 'wait' : 'pointer',
            opacity: loading ? 0.7 : 1,
            boxShadow: '0 4px 14px rgba(0,119,182,0.25)',
            transition: 'all 0.2s',
          }}
        >
          {loading ? '⏳ Executing...' : '▶ Execute Skill'}
        </button>
      </div>

      {result && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          padding: '24px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>Execution Result</h3>
            <span className={
              result.status === 200 && result.data.status === 'SUCCESS'
                ? 'badge badge-green'
                : 'badge badge-red'
            }>
              {result.status === 200 ? result.data.status : `HTTP ${result.status}`}
            </span>
          </div>
          <pre style={{
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 8, padding: 16,
            fontSize: 11, lineHeight: 1.6,
            overflow: 'auto', maxHeight: 400,
            color: 'var(--text-secondary)',
          }}>
            {JSON.stringify(result.data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
