import { useEffect, useMemo, useState } from 'react'
import {
  Circle,
  MapContainer,
  Marker,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'

import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

type AddressSuggestion = {
  label: string
  lat: number
  lon: number
}

type KeywordSuggestion = {
  id: string
  label: string
}

type Poi = {
  id: string
  nom: string
  lat: number
  lon: number
  desc?: string
  site?: string
  num?: string
  mail?: string
  adresse?: string
  siret?: string
  siren?: string
  date?: string
  other1?: string
  other2?: string
}

const DEFAULT_CENTER = { lat: 48.8566, lon: 2.3522 } // Paris fallback

const DEFAULT_MOCK_POIS: Poi[] = [
  {
    id: '1',
    nom: 'Café de la Seine',
    lat: 48.8575,
    lon: 2.3426,
    desc: 'Café au bord de la Seine',
    site: 'https://example.com/cafe',
    num: '+33 1 23 45 67 89',
    mail: 'contact@cafe-seine.fr',
    adresse: '12 Quai de Seine, 75004 Paris',
    siret: '123 456 789 00012',
    siren: '123 456 789',
    date: '2024-02-15',
    other1: 'Terrasse',
    other2: 'WiFi',
  },
  {
    id: '2',
    nom: 'Parc des Lilas',
    lat: 48.8666,
    lon: 2.387,
    desc: 'Parc urbain ombragé',
    site: 'https://example.com/parc',
    num: '+33 1 98 76 54 32',
    mail: 'info@parc-lilas.fr',
    adresse: '2 Rue des Lilas, 75019 Paris',
    siret: '987 654 321 00045',
    siren: '987 654 321',
    date: '2023-11-01',
    other1: 'Jeux enfants',
    other2: 'Concerts l’été',
  },
]

L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

function MapAutoCenter({
  center,
}: {
  center: { lat: number; lon: number }
}) {
  const map = useMap()
  map.setView([center.lat, center.lon])
  return null
}

function App() {
  const [addressQuery, setAddressQuery] = useState('')
  const [addressSuggestions, setAddressSuggestions] = useState<
    AddressSuggestion[]
  >([])
  const [selectedAddress, setSelectedAddress] = useState<AddressSuggestion>()

  const [radius, setRadius] = useState(5)
  const [keywordInput, setKeywordInput] = useState('')
  const [keywordSuggestions, setKeywordSuggestions] = useState<
    KeywordSuggestion[]
  >([])
  const [keywords, setKeywords] = useState<KeywordSuggestion[]>([])

  const [pois, setPois] = useState<Poi[]>(DEFAULT_MOCK_POIS)
  const [isSearching, setIsSearching] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<keyof Poi>('nom')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // Fetch address suggestions (API Adresse)
  useEffect(() => {
    if (addressQuery.trim().length < 3) {
      setAddressSuggestions([])
      return
    }
    const controller = new AbortController()
    const fetchSuggestions = async () => {
      try {
        const res = await fetch(
          `https://api-adresse.data.gouv.fr/search/?q=${encodeURIComponent(
            addressQuery,
          )}&limit=5`,
          { signal: controller.signal },
        )
        if (!res.ok) throw new Error('Adresse API error')
        const data = await res.json()
        const suggestions: AddressSuggestion[] =
          data?.features?.map((feat: any) => ({
            label: feat.properties.label as string,
            lat: feat.geometry.coordinates[1],
            lon: feat.geometry.coordinates[0],
          })) ?? []
        setAddressSuggestions(suggestions)
      } catch (error) {
        if (controller.signal.aborted) return
        console.error(error)
        setAddressSuggestions([])
      }
    }
    const debounce = setTimeout(fetchSuggestions, 250)
    return () => {
      controller.abort()
      clearTimeout(debounce)
    }
  }, [addressQuery])

  // Fetch NAF keyword suggestions
  useEffect(() => {
    if (keywordInput.trim().length < 2) {
      setKeywordSuggestions([])
      return
    }
    const controller = new AbortController()
    const fetchSuggestions = async () => {
      try {
        const res = await fetch(
          `http://127.0.0.1/get_nafs_suggestion?query=${encodeURIComponent(
            keywordInput.trim(),
          )}`,
          { signal: controller.signal },
        )
        if (!res.ok) throw new Error('Suggestion API error')
        const data = await res.json()
        const suggestions: KeywordSuggestion[] = (data?.suggestions ?? []).map(
          (item: any, idx: number) => ({
            id: item.id?.toString() ?? `${item}-${idx}`,
            label: item.label ?? item.toString(),
          }),
        )
        setKeywordSuggestions(suggestions)
      } catch (error) {
        if (controller.signal.aborted) return
        console.error(error)
        // Lightweight fallback when backend is unavailable
        setKeywordSuggestions(
          ['Restaurant', 'Boulangerie', 'Événement', 'Camping', 'Yoga'].map(
            (label, idx) => ({ id: `fallback-${idx}`, label }),
          ),
        )
      }
    }
    const debounce = setTimeout(fetchSuggestions, 200)
    return () => {
      controller.abort()
      clearTimeout(debounce)
    }
  }, [keywordInput])

  const sortedPois = useMemo(() => {
    const data = [...pois]
    data.sort((a, b) => {
      const v1 = (a[sortKey] ?? '') as string
      const v2 = (b[sortKey] ?? '') as string
      const compare = v1.toString().localeCompare(v2.toString(), 'fr', {
        numeric: true,
      })
      return sortDirection === 'asc' ? compare : -compare
    })
    return data
  }, [pois, sortDirection, sortKey])

  const handleSelectAddress = (suggestion: AddressSuggestion) => {
    setSelectedAddress(suggestion)
    setAddressQuery(suggestion.label)
    setAddressSuggestions([])
  }

  const handleAddKeyword = (suggestion: KeywordSuggestion) => {
    if (keywords.some((k) => k.id === suggestion.id)) return
    setKeywords((prev) => [...prev, suggestion])
    setKeywordInput('')
    setKeywordSuggestions([])
  }

  const removeKeyword = (id: string) => {
    setKeywords((prev) => prev.filter((k) => k.id !== id))
  }

  const handleSearch = async () => {
    setIsSearching(true)
    setMessage(null)
    try {
      const payload = {
        address: selectedAddress,
        radiusKm: radius,
        keywords: keywords.map((k) => k.label),
      }
      const res = await fetch('http://127.0.0.1/search_pois', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        throw new Error('API recherche indisponible, utilisation de données de démonstration.')
      }
      const data = await res.json()
      const list: Poi[] = (data?.pois ?? []).map((item: any, idx: number) => ({
        id: item.id?.toString() ?? `poi-${idx}`,
        nom: item.nom ?? 'N/A',
        lat: Number(item.lat),
        lon: Number(item.long ?? item.lon),
        desc: item.desc,
        site: item.site,
        num: item.num,
        mail: item.mail,
        adresse: item.adresse,
        siret: item.siret,
        siren: item.siren,
        date: item.date,
        other1: item.other1,
        other2: item.other2,
      }))
      setPois(list)
      setMessage(`Résultats: ${list.length} point(s) trouvés.`)
    } catch (error) {
      console.error(error)
      setMessage(
        'API indisponible. Affichage de données de démonstration pour continuer.',
      )
      setPois(DEFAULT_MOCK_POIS)
    } finally {
      setIsSearching(false)
    }
  }

  const exportCsv = () => {
    import('xlsx').then(({ utils }) => {
      const ws = utils.json_to_sheet(sortedPois)
      const csv = utils.sheet_to_csv(ws)
      const blob = new Blob([csv], {
        type: 'text/csv;charset=utf-8;',
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'pois.csv')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    })
  }

  const exportExcel = () => {
    import('xlsx').then(({ utils, writeFile }) => {
      const ws = utils.json_to_sheet(sortedPois)
      const wb = utils.book_new()
      utils.book_append_sheet(wb, ws, 'POI')
      writeFile(wb, 'pois.xlsx')
    })
  }

  const toggleSort = (key: keyof Poi) => {
    if (key === sortKey) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDirection('asc')
    }
  }

  const mapCenter = selectedAddress ?? DEFAULT_CENTER

  return (
    <div className="page">
      <header className="header">
        <div className="logo">WEb</div>
        <nav className="nav">
          <a className="nav-item" href="#recherche">
            Recherche
          </a>
          <a className="nav-item" href="#carte">
            Carte
          </a>
          <a className="nav-item" href="#tableau">
            Tableau
          </a>
        </nav>
      </header>

      <main>
        <section id="recherche" className="panel">
          <div className="panel-title">Recherche des points d&apos;intérêt</div>
          <div className="form-grid">
            <div className="field">
              <label>Adresse</label>
              <input
                type="text"
                value={addressQuery}
                placeholder="Saisir une adresse"
                onChange={(e) => setAddressQuery(e.target.value)}
              />
              {addressSuggestions.length > 0 && (
                <div className="suggestion-list">
                  {addressSuggestions.map((s) => (
                    <button
                      key={s.label}
                      className="suggestion-item"
                      onClick={() => handleSelectAddress(s)}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="field">
              <label>
                Rayon (km) <span className="value">{radius.toFixed(1)}</span>
              </label>
              <div className="radius">
                <input
                  type="number"
                  min={0.1}
                  max={70}
                  step={0.1}
                  value={radius}
                  onChange={(e) => setRadius(Number(e.target.value))}
                />
                <input
                  type="range"
                  min={0.1}
                  max={70}
                  step={0.1}
                  value={radius}
                  onChange={(e) => setRadius(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="field">
              <label>Mots-clés (NAF)</label>
              <input
                type="text"
                value={keywordInput}
                placeholder="Tapez pour voir les suggestions"
                onChange={(e) => setKeywordInput(e.target.value)}
              />
              {keywordSuggestions.length > 0 && (
                <div className="suggestion-list">
                  {keywordSuggestions.map((s) => (
                    <button
                      key={s.id}
                      className="suggestion-item"
                      onClick={() => handleAddKeyword(s)}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              )}
              {keywords.length > 0 && (
                <div className="chips">
                  {keywords.map((k) => (
                    <span key={k.id} className="chip">
                      {k.label}
                      <button
                        className="chip-close"
                        onClick={() => removeKeyword(k.id)}
                        aria-label="Supprimer le mot-clé"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="actions">
              <button className="primary" onClick={handleSearch}>
                {isSearching ? 'Recherche...' : 'Rechercher'}
              </button>
              {message && <div className="hint">{message}</div>}
            </div>
          </div>
        </section>

        <section id="carte" className="panel">
          <div className="panel-title">Carte OpenStreetMap</div>
          <div className="map-wrapper">
            <MapContainer
              center={[mapCenter.lat, mapCenter.lon]}
              zoom={12}
              scrollWheelZoom
              style={{ height: '420px', width: '100%' }}
            >
              <MapAutoCenter center={mapCenter} />
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {selectedAddress && (
                <Marker position={[selectedAddress.lat, selectedAddress.lon]}>
                  <Popup>Adresse sélectionnée</Popup>
                </Marker>
              )}
              {selectedAddress && (
                <Circle
                  center={[selectedAddress.lat, selectedAddress.lon]}
                  radius={radius * 1000}
                  pathOptions={{ color: '#2563eb', fillOpacity: 0.08 }}
                />
              )}
              {pois.map((poi) => (
                <Marker key={poi.id} position={[poi.lat, poi.lon]}>
                  <Popup>
                    <div className="popup">
                      <strong>{poi.nom}</strong>
                      {poi.desc && <div>{poi.desc}</div>}
                      {poi.adresse && <div>{poi.adresse}</div>}
                      {poi.site && (
                        <a href={poi.site} target="_blank" rel="noreferrer">
                          Site
                        </a>
                      )}
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </section>

        <section id="tableau" className="panel">
          <div className="panel-header">
            <div className="panel-title">Résultats</div>
            <div className="panel-actions">
              <button onClick={exportCsv}>Exporter CSV</button>
              <button onClick={exportExcel}>Exporter Excel</button>
            </div>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  {(
                    [
                      'nom',
                      'adresse',
                      'lat',
                      'lon',
                      'desc',
                      'site',
                      'num',
                      'mail',
                      'siret',
                      'siren',
                      'date',
                      'other1',
                      'other2',
                    ] as (keyof Poi)[]
                  ).map((key) => (
                    <th key={key} onClick={() => toggleSort(key)}>
                      {key.toUpperCase()}
                      {sortKey === key && (
                        <span className="sort-indicator">
                          {sortDirection === 'asc' ? '▲' : '▼'}
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedPois.map((poi) => (
                  <tr key={poi.id}>
                    <td>{poi.nom}</td>
                    <td>{poi.adresse}</td>
                    <td>{poi.lat}</td>
                    <td>{poi.lon}</td>
                    <td>{poi.desc}</td>
                    <td>
                      {poi.site ? (
                        <a href={poi.site} target="_blank" rel="noreferrer">
                          {poi.site}
                        </a>
                      ) : (
                        ''
                      )}
                    </td>
                    <td>{poi.num}</td>
                    <td>{poi.mail}</td>
                    <td>{poi.siret}</td>
                    <td>{poi.siren}</td>
                    <td>{poi.date}</td>
                    <td>{poi.other1}</td>
                    <td>{poi.other2}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
