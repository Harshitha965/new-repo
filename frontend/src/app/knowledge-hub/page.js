'use client'
import Sidebar from '../../components/layout/Sidebar'
import { useState, useEffect } from 'react'
import { WordLogo, PdfLogo, LockIcon, UnlockIcon } from '../../components/ui/DocLogos'

export default function KnowledgeHubPage() {
  const [files, setFiles] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)

  // HITL Resolution State
  const [activeResolution, setActiveResolution] = useState(null)
  const [scenarios, setScenarios] = useState([])
  const [isFetchingState, setIsFetchingState] = useState(false)
  const [expertDecisions, setExpertDecisions] = useState({})
  const [committedScenarios, setCommittedScenarios] = useState(new Set())
  const [extractedCases, setExtractedCases] = useState([])

  // Accordion & Document View State
  const [expandedFileId, setExpandedFileId] = useState(null)
  const [fileStates, setFileStates] = useState({})
  const [fileInfos, setFileInfos] = useState({})
  const [loadingStates, setLoadingStates] = useState({})
  const [openViewers, setOpenViewers] = useState({})
  const [fullScreenDoc, setFullScreenDoc] = useState(null)
  const [docHtml, setDocHtml] = useState('')
  const [docLoading, setDocLoading] = useState(false)
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null)

  // When fullScreenDoc changes, fetch and render the document client-side
  useEffect(() => {
    if (!fullScreenDoc || !fileInfos[fullScreenDoc]) return

    const info = fileInfos[fullScreenDoc]
    setDocLoading(true)
    setDocHtml('')
    if (pdfBlobUrl) { URL.revokeObjectURL(pdfBlobUrl); setPdfBlobUrl(null) }

    fetch(info.file_url)
      .then(res => res.arrayBuffer())
      .then(async (buffer) => {
        if (info.file_type === 'docx') {
          const mammoth = (await import('mammoth')).default
          const result = await mammoth.convertToHtml({ arrayBuffer: buffer })
          setDocHtml(result.value)
        } else {
          const blob = new Blob([buffer], { type: 'application/pdf' })
          setPdfBlobUrl(URL.createObjectURL(blob))
        }
      })
      .catch(err => {
        console.error('Document render failed:', err)
        setDocHtml('<p style="color:red;padding:40px;">Failed to load document.</p>')
      })
      .finally(() => setDocLoading(false))

    return () => {
      if (pdfBlobUrl) URL.revokeObjectURL(pdfBlobUrl)
    }
  }, [fullScreenDoc])

  const toggleExpand = async (fileId, documentId) => {
    if (expandedFileId === fileId) {
      setExpandedFileId(null)
      return
    }

    setExpandedFileId(fileId)

    if (documentId && !fileStates[documentId] && !loadingStates[documentId]) {
      setLoadingStates(prev => ({ ...prev, [documentId]: true }))
      try {
        const [stateRes, infoRes] = await Promise.all([
          fetch(`http://localhost:8000/api/state/${documentId}`),
          fetch(`http://localhost:8000/api/file-info/${documentId}`)
        ])

        if (stateRes.ok) {
          const data = await stateRes.json()
          setFileStates(prev => ({ ...prev, [documentId]: data }))
        }

        if (infoRes.ok) {
          const infoData = await infoRes.json()
          setFileInfos(prev => ({ ...prev, [documentId]: infoData }))
        }
      } catch (e) {
        console.error('Failed to fetch document state/info:', e)
      }
      setLoadingStates(prev => ({ ...prev, [documentId]: false }))
    }
  }

  // Load state from localStorage on mount
  useEffect(() => {
    const savedQueue = localStorage.getItem('kh_ingestion_queue')
    if (savedQueue) {
      try {
        const parsed = JSON.parse(savedQueue)
        // We must drop the actual File objects because they can't be serialized,
        // but for a queue visualizer, we just need the metadata.
        // Wait, if we drop the File object, we can't upload it if it was queued!
        // We only persist files that are 'done' or 'archived' or 'error'.
        // Queued/uploading files that lost their File object will fail.
        setFiles(parsed.filter(f => f.status !== 'queued' && f.status !== 'uploading'))
      } catch (e) { console.error('Failed to parse queue') }
    }
  }, [])

  // Save state to localStorage on change
  useEffect(() => {
    if (files.length > 0) {
      // Strip out the File object to prevent serialization errors
      const serializableFiles = files.map(f => ({ ...f, file: { name: f.file?.name, size: f.file?.size } }))
      localStorage.setItem('kh_ingestion_queue', JSON.stringify(serializableFiles))
    }
  }, [files])

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        file,
        status: 'queued', // queued, uploading, done, archived, error
        message: '',
        document_id: null
      }))
      setFiles(prev => [...prev, ...newFiles])
    }
  }

  const removeFile = (id) => {
    if (isProcessing) return
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  const handleProcessQueue = async () => {
    if (isProcessing) return
    setIsProcessing(true)

    for (let i = 0; i < files.length; i++) {
      if (files[i].status === 'queued' || files[i].status === 'error') {

        setFiles(prev => prev.map((f, index) =>
          index === i ? { ...f, status: 'uploading', message: 'Ingesting document into pipeline...' } : f
        ))

        const formData = new FormData()
        // If it was loaded from localStorage, f.file might be a dummy object without the actual File blob.
        // But we filtered out queued/error files on reload, so if it's queued, it has the real File.
        if (!files[i].file || !files[i].file.stream) {
          setFiles(prev => prev.map((f, index) =>
            index === i ? { ...f, status: 'error', message: 'File data lost due to refresh. Please re-upload.' } : f
          ))
          continue;
        }

        formData.append('file', files[i].file)

        try {
          const res = await fetch('http://127.0.0.1:8000/api/ingest', {
            method: 'POST',
            body: formData,
          })

          if (!res.ok) {
            const errorData = await res.json()
            throw new Error(errorData.detail || 'Upload failed')
          }

          const data = await res.json()

          setFiles(prev => prev.map((f, index) =>
            index === i ? {
              ...f,
              status: 'done',
              message: 'Success! Paused at HITL Node.',
              document_id: data.document_id
            } : f
          ))
        } catch (err) {
          console.error(err)
          setFiles(prev => prev.map((f, index) =>
            index === i ? { ...f, status: 'error', message: err.message || 'Failed to connect.' } : f
          ))
        }
      }
    }

    setIsProcessing(false)
  }

  const handleOpenResolution = async (file) => {
    setActiveResolution(file)
    setIsFetchingState(true)
    setScenarios([])
    setExpertDecisions({})
    setCommittedScenarios(new Set())
    setExtractedCases([])

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/state/${file.document_id}`)
      if (!res.ok) throw new Error("Failed to fetch LangGraph state")
      const data = await res.json()
      setScenarios(data.synthetic_scenarios || [])
      setExtractedCases(data.parsed_cases || [])
    } catch (e) {
      console.error(e)
      alert("Failed to load synthetic scenarios.")
    }
    setIsFetchingState(false)
  }

  const handleCommitResolution = async (scenario_id) => {
    // Prevent duplicate submissions
    if (committedScenarios.has(scenario_id)) return

    const decision = (expertDecisions[scenario_id] || '').trim()
    if (!decision) {
      alert("Please provide an expert decision for this scenario.")
      return
    }

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/commit?scenario_id=${scenario_id}&expert_decision=${encodeURIComponent(decision)}&archetype=Safety`, {
        method: 'POST'
      })
      if (!res.ok) throw new Error("Commit failed")

      // Mark this scenario as committed (keep it visible but disabled)
      setCommittedScenarios(prev => new Set([...prev, scenario_id]))

      // Check if ALL scenarios are now committed
      const newCommittedCount = committedScenarios.size + 1
      if (newCommittedCount >= scenarios.length) {
        // All done — archive the file and close the modal after a brief delay
        setTimeout(() => {
          setFiles(prev => prev.map(f => f.id === activeResolution.id ? { ...f, status: 'archived', message: 'All scenarios committed to Logic Vault' } : f))
          setActiveResolution(null)
        }, 1500)
      }

    } catch (e) {
      console.error(e)
      alert("Failed to commit resolution.")
    }
  }

  const queuedCount = files.filter(f => f.status === 'queued' || f.status === 'error').length

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar active="/knowledge-hub" />

      <main style={{ flex: 1, padding: '32px 36px', overflow: 'auto', position: 'relative', background: 'var(--bg-base)' }}>
        <div className="fade-up" style={{ marginBottom: 36 }}>
          <h1 style={{ fontSize: 26, fontWeight: 700, marginBottom: 4 }}>Knowledge Hub Ingestion</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
            Upload multiple clinical documents (.pdf or .docx) to batch-process them through the pipeline.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {/* UPLOAD SECTION */}
          <div className="fade-up" style={{
            background: '#FFFFFF', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
            padding: '32px', width: '100%', boxShadow: 'var(--shadow-card)'
          }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 24 }}>Upload Source Material</h2>

            <div style={{
              border: '2px dashed var(--border)', borderRadius: 'var(--radius-md)', padding: '40px',
              textAlign: 'center', marginBottom: 24, background: 'var(--bg-elevated)', transition: 'border-color 0.2s',
            }}>
              <input type="file" accept=".pdf,.docx" multiple onChange={handleFileChange} style={{ display: 'none' }} id="file-upload" />
              <label htmlFor="file-upload" style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <span style={{ fontSize: 32, marginBottom: 12 }}>📁</span>
                <span style={{ fontSize: 15, fontWeight: 500, color: 'var(--accent-primary)', marginBottom: 8 }}>Select multiple files</span>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Supports .PDF and .DOCX</span>
              </label>
            </div>

            <button
              onClick={handleProcessQueue}
              disabled={queuedCount === 0 || isProcessing}
              style={{
                width: '100%', padding: '13px',
                background: (queuedCount === 0 || isProcessing) ? 'var(--bg-elevated)' : 'linear-gradient(135deg, #0D9488, #14B8A6)',
                color: (queuedCount === 0 || isProcessing) ? 'var(--text-secondary)' : '#fff',
                border: 'none', borderRadius: 'var(--radius-sm)', fontWeight: 600, fontSize: 14,
                cursor: (queuedCount === 0 || isProcessing) ? 'not-allowed' : 'pointer', transition: 'all 0.2s',
                boxShadow: (queuedCount === 0 || isProcessing) ? 'none' : '0 4px 16px rgba(13,148,136,0.25)'
              }}
            >
              {isProcessing ? 'Processing Queue...' : `Start Pipeline (${queuedCount} pending)`}
            </button>
          </div>

          {/* QUEUE VISUALIZER SECTION */}
          <div className="fade-up" style={{ width: '100%' }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>Processing Queue</h2>

            {files.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', background: '#FFFFFF', boxShadow: 'var(--shadow-card)' }}>
                No documents in queue.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {files.map((f) => (
                  <div key={f.id} style={{
                    background: '#FFFFFF', border: '1px solid',
                    borderColor: f.status === 'error' ? '#FECACA' :
                      f.status === 'done' ? '#FDE68A' :
                        f.status === 'archived' ? '#BBF7D0' :
                          f.status === 'uploading' ? '#BFDBFE' : 'var(--border)',
                    borderRadius: 'var(--radius-md)', padding: '18px', position: 'relative', overflow: 'hidden',
                    cursor: f.document_id ? 'pointer' : 'default',
                    boxShadow: 'var(--shadow-card)', transition: 'all 0.15s'
                  }}
                    onClick={() => f.document_id && toggleExpand(f.id, f.document_id)}
                  >
                    {f.status === 'uploading' && (
                      <div style={{ position: 'absolute', bottom: 0, left: 0, height: 2, background: 'var(--accent-blue)', width: '100%', animation: 'pulse 2s infinite ease-in-out' }} />
                    )}
                    {f.status === 'done' && (
                      <div style={{ position: 'absolute', bottom: 0, left: 0, height: 2, background: 'var(--accent-orange)', width: '100%', animation: 'pulse 2s infinite ease-in-out' }} />
                    )}
                    {f.status === 'archived' && (
                      <div style={{ position: 'absolute', bottom: 0, left: 0, height: 2, background: 'var(--accent-green)', width: '100%' }} />
                    )}
                    {f.status === 'error' && (
                      <div style={{ position: 'absolute', bottom: 0, left: 0, height: 2, background: 'var(--accent-red)', width: '100%' }} />
                    )}

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontSize: 18 }}>
                          {f.status === 'archived' ? '✅' : f.status === 'done' ? '⚠️' : f.status === 'error' ? '❌' : f.status === 'uploading' ? '⏳' : '📄'}
                        </span>
                        <div>
                          <div style={{ fontSize: 14, fontWeight: 600 }}>{f.file?.name || 'Restored Document'}</div>
                          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{f.file?.size ? (f.file.size / 1024 / 1024).toFixed(2) + ' MB' : 'Size Unknown'}</div>
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        {f.status === 'done' && (
                          <button
                            onClick={(e) => { e.stopPropagation(); handleOpenResolution(f); }}
                            style={{
                              background: 'var(--accent-orange)20', color: 'var(--accent-orange)',
                              border: '1px solid var(--accent-orange)50', padding: '6px 12px',
                              borderRadius: 'var(--radius-sm)', fontSize: 12, fontWeight: 600, cursor: 'pointer'
                            }}
                          >
                            Action Required
                          </button>
                        )}

                        {!isProcessing && (
                          <button onClick={(e) => { e.stopPropagation(); removeFile(f.id); }} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: 16 }}>✕</button>
                        )}

                        {f.document_id && (
                          <span style={{
                            transform: expandedFileId === f.id ? 'rotate(180deg)' : 'rotate(0deg)',
                            transition: 'transform 0.2s',
                            fontSize: 12,
                            color: 'var(--text-secondary)'
                          }}>
                            ▼
                          </span>
                        )}
                      </div>
                    </div>

                    {f.message && (
                      <div style={{
                        fontSize: 12, marginTop: 8,
                        color: f.status === 'error' ? 'var(--accent-red)' :
                          f.status === 'done' ? 'var(--accent-orange)' :
                            f.status === 'archived' ? 'var(--accent-green)' : 'var(--accent-blue)'
                      }}>
                        {f.message}
                      </div>
                    )}

                    {/* Dropdown Content */}
                    {expandedFileId === f.id && (
                      <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }} onClick={(e) => e.stopPropagation()}>
                        {loadingStates[f.document_id] ? (
                          <div style={{ color: 'var(--accent-blue)', fontSize: 14 }}>Loading document content...</div>
                        ) : fileStates[f.document_id] ? (
                          <div className="doc-viewer-enter">
                            <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: 'var(--text-primary)' }}>Document Preview:</h4>

                            {!openViewers[f.document_id] ? (
                              <div className="doc-preview-text" style={{
                                maxHeight: '120px', background: 'var(--bg-elevated)',
                                padding: 16, borderRadius: 'var(--radius-sm)', fontSize: 13, lineHeight: 1.6,
                                color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', border: '1px solid var(--border)',
                                marginBottom: 16, overflow: 'hidden', position: 'relative'
                              }}>
                                {fileStates[f.document_id].raw_chunks?.map(c => c.content).join('\n\n').substring(0, 300) || "No content available."}...
                              </div>
                            ) : null}

                            {/* Logo / Action Badge to Unlock */}
                            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                              <div
                                className="doc-logo-badge"
                                onClick={() => setFullScreenDoc(f.document_id)}
                              >
                                {fileInfos[f.document_id]?.file_type === 'docx' ? (
                                  <WordLogo size={18} />
                                ) : (
                                  <PdfLogo size={18} />
                                )}
                                <span>
                                  View Complete Document
                                </span>
                                <LockIcon size={14} color="var(--text-secondary)" />
                              </div>
                            </div>



                            {fileStates[f.document_id].synthetic_scenarios?.length > 0 && (
                              <div>
                                <h4 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: 'var(--text-primary)' }}>Identified Scenarios:</h4>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                  {fileStates[f.document_id].synthetic_scenarios.map((s, idx) => (
                                    <div key={idx} style={{
                                      fontSize: 13, padding: '12px', background: 'var(--bg-elevated)',
                                      borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)',
                                      color: 'var(--text-secondary)', lineHeight: 1.5
                                    }}>
                                      <strong style={{ color: 'var(--accent-orange)', display: 'block', marginBottom: 4 }}>Scenario {idx + 1}:</strong>
                                      {s.scenario_text}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div style={{ color: 'var(--accent-red)', fontSize: 14 }}>Failed to load content.</div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* HITL RESOLUTION MODAL OVERLAY */}
        {activeResolution && (
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: 40
          }}>
            <div style={{
              background: '#FFFFFF', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
              width: '100%', maxWidth: '800px', maxHeight: '90vh', overflow: 'hidden', display: 'flex', flexDirection: 'column',
              boxShadow: '0 16px 64px rgba(0,0,0,0.15)'
            }}>
              <div style={{ padding: '24px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: 20, fontWeight: 600 }}>Human-in-the-Loop Resolution</h3>
                <button onClick={() => setActiveResolution(null)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-secondary)' }}>✕</button>
              </div>

              <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
                <p style={{ color: 'var(--text-secondary)', marginBottom: 24 }}>
                  The AI pipeline successfully detected clinical decision gaps and generated Synthetic Scenarios to test edge cases.
                  Provide your Expert Decision to commit this logic to the vault.
                </p>

                {isFetchingState ? (
                  <div style={{ textAlign: 'center', padding: 40, color: 'var(--accent-blue)' }}>Fetching state from LangGraph...</div>
                ) : scenarios.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-secondary)' }}>No scenarios found in state.</div>
                ) : (
                  <div>
                    {/* Automatically Extracted Cases Section */}
                    {extractedCases.length > 0 && (
                      <div style={{ marginBottom: 32 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                          <h4 style={{ fontSize: 16, fontWeight: 600 }}>Automatically Extracted Logic</h4>
                          <span className="badge badge-teal">Verified grounding</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                          {extractedCases.map((c, i) => (
                            <div key={i} style={{
                              background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                              padding: 16, borderRadius: 'var(--radius-md)'
                            }}>
                              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4, color: 'var(--accent-teal)' }}>
                                Expert Rule: {c.expert_decision}
                              </div>
                              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                                <strong>Logic:</strong> {c.chain_of_thought.join(' → ')}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                      <h4 style={{ fontSize: 16, fontWeight: 600 }}>Synthetic Scenarios (HITL)</h4>
                      {committedScenarios.size >= scenarios.length ? (
                        <span className="badge badge-green">All committed ✓</span>
                      ) : (
                        <span className="badge badge-amber">{scenarios.length - committedScenarios.size} remaining</span>
                      )}
                    </div>

                    {scenarios.map((scene, idx) => {
                      const isCommitted = committedScenarios.has(scene.id)
                      return (
                        <div key={scene.id || idx} style={{
                          background: isCommitted ? '#F0FDF4' : 'var(--bg-elevated)',
                          padding: 20, borderRadius: 'var(--radius-md)', marginBottom: 24,
                          border: isCommitted ? '1px solid #BBF7D0' : '1px solid var(--border)',
                          opacity: isCommitted ? 0.85 : 1,
                          transition: 'all 0.3s ease',
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: isCommitted ? '#16A34A' : 'var(--accent-orange)' }}>
                              SCENARIO {idx + 1}
                            </div>
                            {isCommitted && (
                              <span className="badge badge-green" style={{ fontSize: 10 }}>✓ Committed to Vault</span>
                            )}
                          </div>
                          <div style={{ fontSize: 15, lineHeight: 1.6, marginBottom: 16 }}>{scene.scenario_text}</div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-secondary)' }}>
                              {isCommitted ? 'Your Submitted Decision:' : 'Your Expert Decision:'}
                            </label>
                            <textarea
                              value={expertDecisions[scene.id] || ''}
                              onChange={(e) => setExpertDecisions(prev => ({ ...prev, [scene.id]: e.target.value }))}
                              disabled={isCommitted}
                              placeholder="Type your medical logic or protocol for handling this specific scenario..."
                              style={{
                                width: '100%', minHeight: 100,
                                background: isCommitted ? '#F0FDF4' : 'var(--bg-card)',
                                border: isCommitted ? '1px solid #BBF7D0' : '1px solid var(--border)',
                                borderRadius: 'var(--radius-sm)', padding: 12,
                                color: isCommitted ? '#16A34A' : 'var(--text-primary)',
                                fontFamily: 'inherit', resize: 'vertical',
                                cursor: isCommitted ? 'not-allowed' : 'text',
                              }}
                            />
                            <button
                              onClick={() => handleCommitResolution(scene.id)}
                              disabled={isCommitted}
                              style={{
                                alignSelf: 'flex-end',
                                background: isCommitted ? '#BBF7D0' : 'var(--accent-green)',
                                color: isCommitted ? '#16A34A' : '#fff',
                                border: 'none',
                                padding: '8px 16px', borderRadius: 'var(--radius-sm)',
                                fontWeight: 600,
                                cursor: isCommitted ? 'not-allowed' : 'pointer',
                                marginTop: 8,
                                transition: 'all 0.3s ease',
                              }}
                            >
                              {isCommitted ? '✓ Committed' : 'Commit Logic to Vault'}
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        {/* FULL SCREEN DOCUMENT VIEWER OVERLAY */}
        {fullScreenDoc && fileInfos[fullScreenDoc] && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(240,244,248,0.97)', backdropFilter: 'blur(12px)',
            zIndex: 9999, display: 'flex', flexDirection: 'column', padding: '24px 32px'
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 24 }}>📄</span>
                <h3 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {fileInfos[fullScreenDoc].filename || 'Document Viewer'}
                </h3>
              </div>
              <button
                onClick={() => setFullScreenDoc(null)}
                style={{
                  background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-primary)',
                  padding: '8px 20px', borderRadius: 'var(--radius-sm)', cursor: 'pointer', fontWeight: 600,
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => { e.currentTarget.style.background = 'var(--bg-card-hover)'; e.currentTarget.style.borderColor = 'var(--border-bright)'; }}
                onMouseOut={(e) => { e.currentTarget.style.background = 'var(--bg-elevated)'; e.currentTarget.style.borderColor = 'var(--border)'; }}
              >
                Exit Full Screen ✕
              </button>
            </div>

            <div style={{ flex: 1, borderRadius: 'var(--radius-lg)', overflow: 'hidden', background: '#fff', border: '1px solid var(--border)' }}>
              {docLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', gap: 16 }}>
                  <div style={{ width: 40, height: 40, border: '3px solid var(--border)', borderTop: '3px solid var(--accent-primary)', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                  <span style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Rendering document...</span>
                </div>
              ) : fileInfos[fullScreenDoc].file_type === 'docx' ? (
                <div
                  style={{
                    padding: '48px 64px', overflowY: 'auto', height: '100%',
                    fontFamily: 'Calibri, Arial, sans-serif', fontSize: '14px', lineHeight: 1.8,
                    color: '#1a1a1a', background: '#fff'
                  }}
                  dangerouslySetInnerHTML={{ __html: docHtml }}
                />
              ) : pdfBlobUrl ? (
                <iframe
                  src={pdfBlobUrl}
                  width="100%"
                  height="100%"
                  frameBorder="0"
                  title="PDF Viewer"
                />
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666' }}>
                  No document to display.
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      <style dangerouslySetInnerHTML={{
        __html: `
        @keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
      `}} />
    </div>
  )
}
