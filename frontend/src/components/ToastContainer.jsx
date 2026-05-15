import React, { useEffect } from 'react'
import useAppStore from '../store/useAppStore.js'

function Toast({ toast }) {
  const removeToast = useAppStore((s) => s.removeToast)
  useEffect(() => {
    const t = setTimeout(() => removeToast(toast.id), 5000)
    return () => clearTimeout(t)
  }, [toast.id, removeToast])

  const cls = toast.type === 'warn' ? 'toast toast-warn'
            : toast.type === 'error' ? 'toast toast-error'
            : 'toast'

  return (
    <div className={cls}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)',
                        marginBottom: 2 }}>
            {toast.type === 'warn' ? 'Warning' : 'New events detected'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            {toast.msg}
          </div>
        </div>
        <button
          onClick={() => removeToast(toast.id)}
          style={{ background: 'none', border: 'none', cursor: 'pointer',
                   color: 'var(--text-muted)', fontSize: 16, lineHeight: 1,
                   padding: '0 2px', flexShrink: 0 }}
        >
          x
        </button>
      </div>
    </div>
  )
}

export default function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts)
  if (!toasts.length) return null
  return (
    <div className="toast-container no-print">
      {toasts.map((t) => <Toast key={t.id} toast={t} />)}
    </div>
  )
}
