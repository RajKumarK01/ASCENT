import { useState } from 'react'

interface PathOption {
  key: string
  title: string
  description: string
  certifications: string[]
}

interface Props {
  profile: any
  onSubmit: (path: string, certification: string) => void
}

export function CertificationPathModal({ profile, onSubmit }: Props) {
  const options: PathOption[] = profile?.path_options ?? []
  const [selectedPath, setSelectedPath] = useState(options[0]?.key ?? 'recommended')
  const [selectedCert, setSelectedCert] = useState(options[0]?.certifications?.[0] ?? '')

  const activeOption = options.find(o => o.key === selectedPath) ?? options[0]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0d1117]/95 backdrop-blur-xl p-6">
      <div className="w-full max-w-3xl rounded-3xl border border-[#30363d] bg-[#161b22] p-6 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.8)]">
        <div className="mb-6">
          <div className="text-3xl font-semibold text-github-text">Choose Your Learning Journey</div>
          <p className="mt-3 text-sm text-github-muted max-w-2xl">Pick the path that fits your role, skills, and certification goals. This selection helps ASCENT personalise your study plan and assessment experience.</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 mb-6">
          {options.map(option => (
            <button key={option.key} type="button"
              onClick={() => {
                setSelectedPath(option.key)
                setSelectedCert(option.certifications[0] ?? '')
              }}
              className={`rounded-3xl border p-5 text-left transition ${selectedPath === option.key ? 'border-github-blue bg-github-blue/10 shadow-lg shadow-github-blue/10' : 'border-github-border bg-[#151a22] hover:border-github-blue/40 hover:bg-github-bg'}`}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xl font-semibold text-github-text">{option.title}</div>
                  <p className="text-sm text-github-muted mt-2">{option.description}</p>
                </div>
                <span className={`text-xs font-semibold rounded-full px-3 py-1 ${selectedPath === option.key ? 'bg-github-blue/20 text-github-blue' : 'bg-github-border/70 text-github-muted'}`}>
                  {selectedPath === option.key ? 'Selected' : 'Choose'}
                </span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {option.certifications.map(cert => (
                  <span key={cert} className="rounded-full border border-github-border/60 bg-github-border/10 px-3 py-1 text-xs text-github-text">{cert}</span>
                ))}
              </div>
            </button>
          ))}
        </div>

        {activeOption?.certifications?.length > 1 && selectedPath === 'custom' && (
          <div className="mb-6 rounded-3xl border border-github-border bg-github-bg p-5">
            <div className="text-sm text-github-muted mb-3">Select your custom certification target</div>
            <select
              value={selectedCert}
              onChange={e => setSelectedCert(e.target.value)}
              className="w-full rounded-2xl border border-github-border bg-[#12171f] px-4 py-3 text-sm text-github-text focus:outline-none focus:ring-2 focus:ring-github-blue"
            >
              {activeOption.certifications.map(cert => (
                <option key={cert} value={cert}>{cert}</option>
              ))}
            </select>
          </div>
        )}

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-sm text-github-muted">{profile?.message ?? 'Select a path to continue.'}</div>
          <button
            type="button"
            onClick={() => onSubmit(selectedPath, selectedCert)}
            className="inline-flex items-center justify-center rounded-3xl bg-github-blue px-5 py-3 text-sm font-semibold text-github-bg transition hover:bg-github-blue/80"
          >
            Confirm path
          </button>
        </div>
      </div>
    </div>
  )
}
