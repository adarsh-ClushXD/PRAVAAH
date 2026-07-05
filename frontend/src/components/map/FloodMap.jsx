/**
 * PRAVAAH Interactive Flood Map Component
 * Leaflet map showing West Bengal with risk-colored district overlays.
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { MapContainer, TileLayer, GeoJSON, Tooltip, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { usePravaahStore } from '../../store/pravaahStore'
import { getRiskFillColor, getRiskOpacity } from '../../utils/riskColorScale'
import RiverGaugeMarkers from './RiverGaugeMarkers'
import MapLegend from './MapLegend'

const WB_CENTER = [23.5, 87.9]
const WB_ZOOM = 7

// Bundled simplified GeoJSON for West Bengal districts
// In production this would be loaded from /api/v1/geojson
const WB_GEOJSON_URL = '/wb_districts.geojson'

function MapZoomController({ districtId, districts }) {
  const map = useMap()
  useEffect(() => {
    if (!districtId || !districts.length) return
    const district = districts.find(d => d.district_id === districtId)
    if (district) {
      map.setView([district.lat, district.lon], 9, { animate: true, duration: 0.8 })
    }
  }, [districtId, districts, map])
  return null
}

export default function FloodMap() {
  const { districts, selectedDistrictId, riverStations, selectDistrict, mapZoomDistrict } = usePravaahStore()
  const [geojsonData, setGeojsonData] = useState(null)
  const geoJsonRef = useRef(null)

  // Build lookup for risk data by district name
  const riskByName = useCallback(() => {
    const lookup = {}
    districts.forEach(d => {
      lookup[d.district_name.toLowerCase()] = d
      lookup[d.district_id] = d
    })
    return lookup
  }, [districts])

  useEffect(() => {
    // Load bundled GeoJSON
    fetch(WB_GEOJSON_URL)
      .then(r => r.json())
      .then(data => setGeojsonData(data))
      .catch(() => {
        // Use inline simplified geometry fallback — empty FeatureCollection
        setGeojsonData({ type: 'FeatureCollection', features: [] })
      })
  }, [])

  // Re-color GeoJSON when district risk data changes
  useEffect(() => {
    if (!geoJsonRef.current) return
    geoJsonRef.current.resetStyle()
  }, [districts])

  const styleFeature = useCallback((feature) => {
    const lookup = riskByName()
    const props = feature?.properties || {}
    const nameKey = (props.DISTRICT || props.NAME_2 || props.district || '').toLowerCase().replace(/\s+/g, '_')
    const districtData = lookup[nameKey] || lookup[props.district_id] || null
    const riskScore = districtData?.composite_flood_risk_index

    const isSelected = districtData?.district_id === selectedDistrictId

    return {
      fillColor: getRiskFillColor(riskScore),
      fillOpacity: getRiskOpacity(riskScore),
      color: isSelected ? '#00D4FF' : 'rgba(255,255,255,0.1)',
      weight: isSelected ? 2.5 : 0.8,
      dashArray: null,
    }
  }, [districts, selectedDistrictId])

  const onEachFeature = useCallback((feature, layer) => {
    const lookup = riskByName()
    const props = feature?.properties || {}
    const nameKey = (props.DISTRICT || props.NAME_2 || props.district || '').toLowerCase().replace(/\s+/g, '_')
    const districtData = lookup[nameKey] || lookup[props.district_id] || null

    if (districtData) {
      layer.on({
        click: () => selectDistrict(districtData.district_id),
        mouseover: (e) => {
          e.target.setStyle({ fillOpacity: 0.9, weight: 2, color: '#00D4FF' })
        },
        mouseout: (e) => {
          if (geoJsonRef.current) geoJsonRef.current.resetStyle(e.target)
        },
      })
    }
  }, [riskByName, selectDistrict])

  return (
    <div className="relative w-full h-full">
      <MapContainer
        center={WB_CENTER}
        zoom={WB_ZOOM}
        className="w-full h-full"
        style={{ background: '#050c1a' }}
        zoomControl={false}
      >
        {/* Dark satellite-style tile layer */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains="abcd"
          maxZoom={19}
        />

        {/* District GeoJSON Layer */}
        {geojsonData && geojsonData.features && geojsonData.features.length > 0 && (
          <GeoJSON
            ref={geoJsonRef}
            data={geojsonData}
            style={styleFeature}
            onEachFeature={onEachFeature}
            key={districts.length}
          />
        )}

        {/* River Gauge Markers */}
        <RiverGaugeMarkers stations={riverStations} />

        {/* Auto-zoom on district selection */}
        <MapZoomController districtId={mapZoomDistrict} districts={districts} />
      </MapContainer>

      {/* Map Legend */}
      <MapLegend />

      {/* No data overlay when GeoJSON has no features */}
      {geojsonData && geojsonData.features?.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="glass-panel px-6 py-4 text-center">
            <p className="text-slate-400 text-sm">Loading district boundaries…</p>
            <p className="text-slate-500 text-xs mt-1">
              Place <code className="text-cyan-glow">wb_districts.geojson</code> in{' '}
              <code className="text-cyan-glow">frontend/public/</code>
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
