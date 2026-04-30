'use client'
import { useState, useEffect } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export default function GuardrailEditor() {
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSkills()
  }, [])

  const fetchSkills = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/skills`)
      const data = await res.json()
      setSkills(data)
    } catch (err) {
      console.error("Failed to fetch skills", err)
    } finally {
      setLoading(false)
    }
  }

  const toggleSkill = async (skillName) => {
    try {
      const res = await fetch(`${API_BASE}/admin/skills/${skillName}/toggle`, {
        method: 'POST'
      })
      const data = await res.json()
      setSkills(skills.map(s => s.skill_name === skillName ? { ...s, is_active: data.is_active } : s))
    } catch (err) {
      console.error("Failed to toggle skill", err)
    }
  }

  if (loading) {
    return <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading skill definitions...</p>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {skills.map(skill => (
        <div key={skill.id} style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          padding: '16px 20px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          transition: 'all 0.2s',
        }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
              {skill.skill_name}
            </div>
            <span className={skill.is_active ? 'badge badge-green' : 'badge badge-red'}>
              {skill.is_active ? 'ACTIVE' : 'DISABLED'}
            </span>
          </div>
          <label style={{ position: 'relative', display: 'inline-block', width: 48, height: 24, flexShrink: 0 }}>
            <input
              type="checkbox"
              checked={skill.is_active}
              onChange={() => toggleSkill(skill.skill_name)}
              style={{ opacity: 0, width: 0, height: 0 }}
            />
            <span style={{
              position: 'absolute', cursor: 'pointer',
              top: 0, left: 0, right: 0, bottom: 0,
              background: skill.is_active ? '#10B981' : '#E2E8F0',
              transition: '0.3s', borderRadius: 24,
            }}>
              <span style={{
                position: 'absolute',
                content: '""',
                height: 18, width: 18,
                left: skill.is_active ? 26 : 3,
                bottom: 3,
                background: '#fff',
                transition: '0.3s',
                borderRadius: '50%',
                boxShadow: '0 1px 3px rgba(0,0,0,0.15)',
              }} />
            </span>
          </label>
        </div>
      ))}
      {skills.length === 0 && (
        <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
          No skills found. Start the backend to register skills.
        </p>
      )}
    </div>
  )
}
