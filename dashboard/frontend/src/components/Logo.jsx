import { useState } from 'react'
import { logoUrl } from '../lib/api'

export default function Logo({ ticker, size = 32 }) {
  const [err, setErr] = useState(false)
  const url = logoUrl(ticker)

  if (!url || err) {
    return (
      <div
        className="signal-logo-placeholder"
        style={{ width: size, height: size, fontSize: Math.max(9, size * 0.3) }}
      >
        {ticker?.slice(0, 3)}
      </div>
    )
  }
  return (
    <img
      src={url}
      alt={ticker}
      width={size}
      height={size}
      className="signal-logo"
      style={{ width: size, height: size }}
      onError={() => setErr(true)}
    />
  )
}
