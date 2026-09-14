import { Link, Route, Routes } from 'react-router-dom'
import { OfferDetailsPage } from './pages/OfferDetailsPage'
import { SearchPage } from './pages/SearchPage'

function App() {
  return (
    <div className="app">
      <header className="naglowek">
        <Link to="/" className="naglowek__logo">
          Pobyty Sanatoryjne
        </Link>
        <p className="naglowek__podtytul">Wyszukiwarka rzeczywistych ofert sanatoryjnych</p>
      </header>

      <main className="tresc">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/oferta/:id" element={<OfferDetailsPage />} />
        </Routes>
      </main>

      <footer className="stopka">
        <p>Ceny i dostępność pochodzą ze stron ośrodków i mogą się zmienić — zawsze sprawdzaj u źródła.</p>
      </footer>
    </div>
  )
}

export default App
