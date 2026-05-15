import React, { useState, useEffect, useCallback } from 'react'
import { GeoJSON, useMap } from 'react-leaflet'

// ISO2 -> ISO3 mapping for GADM URLs
const ISO3 = {
  DJ:'DJI', ER:'ERI', ET:'ETH', KE:'KEN',
  RW:'RWA', SO:'SOM', SS:'SSD', SD:'SDN',
  TZ:'TZA', UG:'UGA', BI:'BDI',
}

const GADM_BASE = 'https://geodata.ucdavis.edu/gadm/gadm4.1/json'

// Cache fetched GeoJSON in memory to avoid repeated network calls
const geoCache = {}

async function fetchDistricts(iso2) {
  if (geoCache[iso2]) return geoCache[iso2]
  const iso3 = ISO3[iso2]
  if (!iso3) return null
  const url = GADM_BASE + '/gadm41_' + iso3 + '_1.json'
  const res  = await fetch(url, { signal: AbortSignal.timeout(15000) })
  if (!res.ok) throw new Error('HTTP ' + res.status)
  const data = await res.json()
  geoCache[iso2] = data
  return data
}

const DISTRICT_STYLE = {
  color:       '#7F77DD',
  weight:      0.8,
  fillColor:   '#7F77DD',
  fillOpacity: 0.04,
  dashArray:   '3 4',
}

export function DistrictLayer({ iso2, lightMode }) {
  const [geo,     setGeo]     = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    if (!iso2) { setGeo(null); setError(null); return }
    setLoading(true)
    setError(null)
    fetchDistricts(iso2)
      .then((data) => { setGeo(data); setLoading(false) })
      .catch((err) => {
        setError('Could not load district boundaries: ' + err.message)
        setLoading(false)
      })
  }, [iso2])

  if (!geo) return null

  const style = {
    ...DISTRICT_STYLE,
    color: lightMode ? '#534AB7' : '#7F77DD',
  }

  return (
    <GeoJSON
      key={'districts-' + iso2}
      data={geo}
      style={() => style}
    />
  )
}

// Control panel for the district toggle (rendered outside MapContainer)
export function DistrictControl({ iso2, lightMode }) {
  const [distOn, setDistOn] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error,   setError]  = useState(null)
  const [geo,     setGeo]    = useState(null)

  useEffect(() => {
    if (!distOn || !iso2) return
    if (geoCache[iso2]) { setGeo(geoCache[iso2]); return }
    setLoading(true)
    setError(null)
    fetchDistricts(iso2)
      .then((data) => { setGeo(data); setLoading(false) })
      .catch((err) => {
        setError('Load failed')
        setLoading(false)
      })
  }, [distOn, iso2])

  useEffect(() => {
    if (!iso2) { setDistOn(false); setGeo(null) }
  }, [iso2])

  return { distOn, setDistOn, geo, loading, error }
}
