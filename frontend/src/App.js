import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [address, setAddress] = useState('');
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 600);
  const containerRef = useRef(null);
  const debounceTimeoutRef = useRef(null);

  const BACKEND_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  const fetchEstimate = async (selectedAddress = address) => {
    if (!selectedAddress.trim()) {
      setError('Please enter an address.');
      return;
    }

    setLoading(true);
    setError(null);
    setEstimate(null);
    setSuggestions([]);
    setShowSuggestions(false);

    try {
      const response = await fetch(`${BACKEND_BASE_URL}/estimate?address=${encodeURIComponent(selectedAddress)}`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch estimate');
      }

      const data = await response.json();
      setEstimate(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSuggestions = async (input) => {
    if (!input.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      const proxyUrl = `${BACKEND_BASE_URL}/google-autocomplete?input=${encodeURIComponent(input)}`;
      const response = await fetch(proxyUrl);
      const data = await response.json();

      if (data.status === 'OK' && data.predictions && data.predictions.length > 0) {
        setSuggestions(data.predictions.map(prediction => prediction.description));
        setShowSuggestions(true);
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (err) {
      console.error("Error fetching suggestions:", err);
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleAddressInputChange = (e) => {
    const input = e.target.value;
    setAddress(input);
    setActiveSuggestion(-1);

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      fetchSuggestions(input);
    }, 300);
  };

  const handleSelectSuggestion = (selectedSuggestion) => {
    setAddress(selectedSuggestion);
    setSuggestions([]);
    setShowSuggestions(false);
    setActiveSuggestion(-1);
  };

  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      setActiveSuggestion((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      setActiveSuggestion((prev) => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      if (activeSuggestion >= 0 && activeSuggestion < suggestions.length) {
        handleSelectSuggestion(suggestions[activeSuggestion]);
        e.preventDefault();
      }
    }
  };

  const parseSaleHistory = (jsonString) => {
    try {
      return JSON.parse(jsonString);
    } catch {
      return {};
    }
  };

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 600);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, []);

  return (
    <div className="App">
      <div className="header-mobile">
        <span className="bank">MELNIK_RE_APP</span>
        <span className="phone">(555) 123-4567</span>
      </div>

      <div className={isMobile ? "main-mobile" : "main-desktop"} ref={containerRef}>
        <h2 style={{ textAlign: 'left', fontWeight: 800, fontSize: isMobile ? '2rem' : '1.5rem', margin: '0 0 18px 0' }}>
          Enter your property address
        </h2>

        <input
          className={isMobile ? "input-mobile" : "input-desktop"}
          type="text"
          placeholder="5500 Grand Lake Dr, San Antonio, TX"
          value={address}
          onChange={handleAddressInputChange}
          onFocus={() => address.trim() && fetchSuggestions(address)}
          onKeyDown={handleKeyDown}
        />

        {showSuggestions && suggestions.length > 0 && (
          <ul className="suggestion-list">
            {suggestions.map((suggestion, index) => (
              <li
                key={index}
                onClick={() => handleSelectSuggestion(suggestion)}
                onMouseEnter={() => setActiveSuggestion(index)}
                onMouseLeave={() => setActiveSuggestion(-1)}
                className={index === activeSuggestion ? "active-suggestion" : ""}
              >
                {suggestion}
              </li>
            ))}
          </ul>
        )}

        <button
          className={isMobile ? "button-mobile" : "button-desktop"}
          onClick={() => fetchEstimate()}
          disabled={loading || !address.trim()}
        >
          {loading ? 'Valuating...' : 'Get Estimate'}
        </button>
      </div>

      {error && <p style={{ color: 'red', fontSize: '1.1em', marginTop: '20px' }}>Error: {error}</p>}
      {estimate && (
        <div className="estimate-result">
          <h2>Valuation Result:</h2>
          <div style={{ textAlign: 'left', lineHeight: '1.8' }}>
            <p><strong>Address:</strong> {estimate.formattedAddress || estimate.address}</p>
            <p><strong>Estimate:</strong> {estimate.valuation ? `${estimate.valuation} ${estimate.currency}` : 'No data'}</p>
            <p><strong>Property type:</strong> {estimate.property_type || 'No data'}</p>
            <p><strong>Bedrooms:</strong> {estimate.bedrooms || 'No data'}</p>
            <p><strong>Bathrooms:</strong> {estimate.bathrooms || 'No data'}</p>
            <p><strong>Area (sq.ft):</strong> {estimate.square_footage || 'No data'}</p>
            <p><strong>Lot size (sq.ft):</strong> {estimate.lot_size || 'No data'}</p>
            <p><strong>Year built:</strong> {estimate.year_built || 'No data'}</p>
            <p><strong>Last sale date:</strong> {estimate.last_sale_date ? new Date(estimate.last_sale_date).toLocaleDateString() : 'No data'}</p>
            <p><strong>Valuation date:</strong> {estimate.created_at ? new Date(estimate.created_at).toLocaleString() : 'N/A'}</p>

            {estimate.sale_history_json && Object.keys(parseSaleHistory(estimate.sale_history_json)).length > 0 && (
              <div style={{ marginTop: '20px', borderTop: '1px dashed #e0e0e0', paddingTop: '20px' }}>
                <h3>Sale History:</h3>
                <ul style={{ listStyleType: 'none', padding: 0 }}>
                  {Object.entries(parseSaleHistory(estimate.sale_history_json)).map(([dateKey, sale]) => (
                    <li key={dateKey} style={{ marginBottom: '10px', backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '5px' }}>
                      <strong>Event:</strong> {sale.event || 'Sale'}<br />
                      <strong>Date:</strong> {sale.date ? new Date(sale.date).toLocaleDateString() : 'N/A'}<br />
                      <strong>Price:</strong> {sale.price ? `${sale.price} ${estimate.currency}` : 'N/A'}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;