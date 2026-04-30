'use client'
import { useState, useEffect } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export default function ExecutionLogViewer() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedLog, setExpandedLog] = useState(null)

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/logs`)
      const data = await res.json()
      setLogs(data)
    } catch (err) {
      console.error("Failed to fetch logs", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchLogs, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading execution logs...</p>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {logs.map(log => (
        <div
          key={log.id}
          onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            padding: '16px 20px',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                {log.skill_name}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                {log.created_at ? new Date(log.created_at).toLocaleString() : 'Unknown time'}
              </div>
            </div>
            <span className={
              log.status === 'SUCCESS' ? 'badge badge-green' :
              log.status === 'FAILED' ? 'badge badge-red' :
              'badge badge-amber'
            }>
              {log.status}
            </span>
          </div>
          
          {expandedLog === log.id && (
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>
                Raw Payload:
              </div>
              <pre style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                borderRadius: 8, padding: 12,
                fontSize: 11, overflow: 'auto',
                color: 'var(--text-secondary)',
              }}>
                {JSON.stringify(log.raw_payload, null, 2)}
              </pre>
              
              {log.error_trace && (
                <>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent-red)', marginTop: 12, marginBottom: 6 }}>
                    Error Trace:
                  </div>
                  <pre style={{
                    background: '#FEF2F2',
                    border: '1px solid #FECACA',
                    borderRadius: 8, padding: 12,
                    fontSize: 11, color: '#DC2626',
                  }}>
                    {log.error_trace}
                  </pre>
                </>
              )}
            </div>
          )}
        </div>
      ))}
      {logs.length === 0 && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          padding: '32px', textAlign: 'center',
        }}>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            No execution logs yet. Execute a skill from the Sandbox tab.
          </p>
        </div>
      )}
    </div>
  )
}
