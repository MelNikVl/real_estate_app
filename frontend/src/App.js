// real_estate_app/frontend/src/App.js

import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [address, setAddress] = useState('');
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]); // Suggestions state
  const [showSuggestions, setShowSuggestions] = useState(false); // Show suggestions
  const [activeSuggestion, setActiveSuggestion] = useState(-1); // For keyboard navigation

  // Google API Key теперь не нужен на фронтенде напрямую
  // const GOOGLE_API_KEY = process.env.REACT_APP_GOOGLE_API_KEY; // Эту строку можно удалить или закомментировать

  // Реф для дебаунсинга запросов к Google API
  const debounceTimeoutRef = useRef(null);

  // URL вашего FastAPI бэкенда (без изменений)
  // В .env.production у вас должно быть REACT_APP_API_BASE_URL=http://localhost:8000
  const BACKEND_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  // Функция для запроса оценки недвижимости с бэкенда (без изменений)
  const fetchEstimate = async (selectedAddress = address) => {
    if (!selectedAddress.trim()) {
      setError('Please enter an address.');
      return;
    }

    setLoading(true);
    setError(null);
    setEstimate(null);
    setSuggestions([]); // Очищаем подсказки после отправки запроса
    setShowSuggestions(false); // Скрываем подсказки

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

  // НОВАЯ ФУНКЦИЯ: для получения автоподсказок от вашего бэкенда (который проксирует Google API)
  const fetchSuggestions = async (input) => {
    // API Key теперь не проверяем здесь, так как он на бэкенде
    if (!input.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      // Запрос теперь идет на ваш бэкенд
      const proxyUrl = `${BACKEND_BASE_URL}/google-autocomplete?input=${encodeURIComponent(input)}`;

      const response = await fetch(proxyUrl);
      const data = await response.json(); // Ожидаем JSON ответ от вашего бэкенда

      if (data.status === 'OK' && data.predictions && data.predictions.length > 0) {
        setSuggestions(data.predictions.map(prediction => prediction.description));
        setShowSuggestions(true);
      } else if (data.status === 'ZERO_RESULTS') {
        console.log("Google Places API (via backend): No results for this input.");
        setSuggestions([]);
        setShowSuggestions(false);
      } else {
        console.error("Google Places API error (via backend):", data.status, data.error_message || "Unknown error");
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (err) {
      console.error("Error fetching Google Places suggestions (via backend):", err);
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Обработчик изменения поля ввода с дебаунсингом (без изменений)
  const handleAddressInputChange = (e) => {
    const input = e.target.value;
    setAddress(input);
    setActiveSuggestion(-1); // Сбросить активную подсказку при вводе

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      fetchSuggestions(input);
    }, 300);
  };

  // Обработчик выбора подсказки (без изменений)
  const handleSelectSuggestion = (selectedSuggestion) => {
    setAddress(selectedSuggestion);
    setSuggestions([]);
    setShowSuggestions(false);
    setActiveSuggestion(-1);
  };

  // Обработчик нажатий клавиш для навигации по подсказкам
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

  // Функция для парсинга истории продаж (без изменений)
  const parseSaleHistory = (jsonString) => {
    try {
      return JSON.parse(jsonString);
    } catch (e) {
      console.error("Failed to parse sale history JSON:", e);
      return {};
    }
  };

  return (
    <div className="App">
      {/* Mobile header */}
      <div className="header-mobile">
        <span className="bank">BANK</span>
        <span className="phone">(555) 123-4567</span>
      </div>
      <div className="main-mobile">
        <h2 style={{ textAlign: 'left', fontWeight: 800, fontSize: '2rem', margin: '0 0 18px 0' }}>Enter your property address</h2>
        <input
          className="input-mobile"
          type="text"
          placeholder="1234 Elm St, Springfield, IL"
          value={address}
          onChange={handleAddressInputChange}
          onFocus={() => address.trim() && fetchSuggestions(address)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 100)}
          onKeyDown={handleKeyDown}
        />
        {showSuggestions && suggestions.length > 0 && (
          <ul style={{
            position: 'relative',
            background: '#fff',
            border: '1px solid #eee',
            borderRadius: '12px',
            listStyle: 'none',
            padding: 0,
            margin: 0,
            maxHeight: '180px',
            overflowY: 'auto',
            zIndex: 100
          }}>
            {suggestions.map((suggestion, index) => (
              <li
                key={index}
                onClick={() => handleSelectSuggestion(suggestion)}
                style={{
                  padding: '12px 16px',
                  borderBottom: '1px solid #f0f0f0',
                  cursor: 'pointer',
                  background: index === activeSuggestion ? '#f8f9fb' : '#fff',
                  fontWeight: index === activeSuggestion ? 'bold' : 'normal'
                }}
                onMouseEnter={() => setActiveSuggestion(index)}
                onMouseLeave={() => setActiveSuggestion(-1)}
              >
                {suggestion}
              </li>
            ))}
          </ul>
        )}
        <button
          className="button-mobile"
          onClick={() => fetchEstimate()}
          disabled={loading || !address.trim()}
        >
          {loading ? 'Valuating...' : 'Get Estimate'}
        </button>
        {error && <div style={{ color: 'red', fontSize: '1em', margin: '10px 0' }}>Error: {error}</div>}
        {estimate && (
          <>
            <div className="estimate-label">Estimated Home Value</div>
            <div className="estimate-value">{estimate.estimated_value ? `$${estimate.estimated_value.toLocaleString()}` : 'No data'}</div>
            <div className="info-box">
              <svg width="28" height="28" fill="none" viewBox="0 0 28 28"><circle cx="14" cy="14" r="14" fill="#e3edfc"/><text x="14" y="19" textAnchor="middle" fontSize="18" fontWeight="bold" fill="#3b82f6">🙂</text></svg>
              Spring is a great time to sell your home.
            </div>
            <div className="report-block">
              <div style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: 10 }}>Get your free report</div>
              <input className="input-email" type="email" placeholder="Email address" />
              <button className="button-report">Get Report</button>
            </div>
            <div className="expert-link">
              <svg width="20" height="20" fill="none" viewBox="0 0 20 20"><circle cx="10" cy="10" r="10" fill="#eee"/><path d="M10 10a3 3 0 100-6 3 3 0 000 6zM10 12c-2.33 0-7 1.17-7 3.5V18h14v-2.5C17 13.17 12.33 12 10 12z" fill="#888"/></svg>
              Expert consultation
            </div>
          </>
        )}
      </div>

      <div style={{ marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{ position: 'relative', width: '400px', maxWidth: 'calc(100% - 150px)' }}>
          <input
            type="text"
            placeholder="Enter address (e.g. 5500 Grand Lake Dr, San Antonio, TX 78244)"
            value={address}
            onChange={handleAddressInputChange}
            onFocus={() => address.trim() && fetchSuggestions(address)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 100)}
            onKeyDown={handleKeyDown}
            style={{
              padding: '12px 15px',
              width: '100%',
              marginRight: '15px',
              borderRadius: '8px',
              border: '1px solid #a0a0a0',
              boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.1)',
              fontSize: '16px',
              boxSizing: 'border-box'
            }}
          />
          {showSuggestions && suggestions.length > 0 && (
            <ul style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              backgroundColor: 'white',
              border: '1px solid #a0a0a0',
              borderRadius: '8px',
              listStyle: 'none',
              padding: '0',
              margin: '5px 0 0 0',
              maxHeight: '200px',
              overflowY: 'auto',
              zIndex: 100
            }}>
              {suggestions.map((suggestion, index) => (
                <li
                  key={index}
                  onClick={() => handleSelectSuggestion(suggestion)}
                  style={{
                    padding: '10px 15px',
                    borderBottom: '1px solid #eee',
                    cursor: 'pointer',
                    textAlign: 'left',
                    backgroundColor: index === activeSuggestion ? '#e6f7ff' : 'white',
                    fontWeight: index === activeSuggestion ? 'bold' : 'normal'
                  }}
                  onMouseEnter={() => setActiveSuggestion(index)}
                  onMouseLeave={() => setActiveSuggestion(-1)}
                >
                  {suggestion}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button
          onClick={() => fetchEstimate()}
          disabled={loading || !address.trim()}
          style={{
            padding: '12px 25px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            transition: 'background-color 0.3s ease, transform 0.2s ease',
            marginTop: '15px'
          }}
        >
          {loading ? 'Valuating...' : 'Get Estimate'}
        </button>
      </div>

      {error && <p style={{ color: 'red', fontSize: '1.1em', marginTop: '20px' }}>Error: {error}</p>}

      {estimate && (
        <div style={{
          border: '1px solid #dcdcdc',
          padding: '25px',
          borderRadius: '12px',
          maxWidth: '600px',
          margin: '30px auto',
          backgroundColor: '#ffffff',
          boxShadow: '0 6px 12px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>Valuation Result:</h2>
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
                <h3 style={{ color: '#2c3e50', marginBottom: '15px' }}>Sale History:</h3>
                <ul style={{ listStyleType: 'none', padding: 0 }}>
                  {Object.entries(parseSaleHistory(estimate.sale_history_json)).map(([dateKey, sale]) => (
                    <li key={dateKey} style={{ marginBottom: '10px', backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '5px' }}>
                      <strong>Event:</strong> {sale.event || 'Sale'} <br />
                      <strong>Date:</strong> {sale.date ? new Date(sale.date).toLocaleDateString() : 'N/A'} <br />
                      <strong>Price:</strong> {sale.price ? `${sale.price} ${estimate.currency}` : 'N/A'}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

    {/* Features block in English */}
    <div style={{
      background: '#eaf0fa',
      borderRadius: '18px',
      maxWidth: 600,
      margin: '40px auto 0',
      padding: '40px 20px',
      boxShadow: '0 4px 16px rgba(44,62,80,0.07)',
      textAlign: 'center'
    }}>
      <div style={{ marginBottom: 40 }}>
        <div style={{ background: '#e3edfc', borderRadius: '50%', width: 60, height: 60, margin: '0 auto 18px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="32" height="32" fill="none" viewBox="0 0 32 32"><path d="M7 25l7.5-7.5 5 5L27 12" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/><circle cx="16" cy="16" r="15" stroke="#e3edfc" strokeWidth="2"/></svg>
        </div>
        <h2 style={{ fontWeight: 700, fontSize: 22, margin: 0 }}>Accurate Valuations</h2>
        <div style={{ color: '#444', fontSize: 16, marginTop: 8 }}>Machine learning algorithms analyze millions of transactions</div>
      </div>
      <div style={{ marginBottom: 40 }}>
        <div style={{ background: '#e6fce6', borderRadius: '50%', width: 60, height: 60, margin: '0 auto 18px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="32" height="32" fill="none" viewBox="0 0 32 32"><circle cx="15" cy="15" r="8" stroke="#22c55e" strokeWidth="2.5"/><path d="M28 28l-7-7" stroke="#22c55e" strokeWidth="2.5" strokeLinecap="round"/></svg>
        </div>
        <h2 style={{ fontWeight: 700, fontSize: 22, margin: 0 }}>Instant Results</h2>
        <div style={{ color: '#444', fontSize: 16, marginTop: 8 }}>Get your estimate in seconds, no waiting</div>
      </div>
      <div>
        <div style={{ background: '#f6eaff', borderRadius: '50%', width: 60, height: 60, margin: '0 auto 18px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="32" height="32" fill="none" viewBox="0 0 32 32"><path d="M8 14l8-8 8 8" stroke="#a259f7" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/><rect x="8" y="14" width="16" height="10" rx="2" stroke="#a259f7" strokeWidth="2.5"/></svg>
        </div>
        <h2 style={{ fontWeight: 700, fontSize: 22, margin: 0 }}>Full Information</h2>
        <div style={{ color: '#444', fontSize: 16, marginTop: 8 }}>Object details, price history, and neighborhood analytics</div>
      </div>
    </div>
  </div>
  );
}

export default App;
