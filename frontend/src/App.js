// real_estate_app/frontend/src/App.js

import React, { useState } from 'react';
import './App.css'; // Оставим стандартный CSS, если он есть

function App() {
  const [address, setAddress] = useState('');
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchEstimate = async () => {
    setLoading(true);
    setError(null);
    setEstimate(null); // Сбрасываем предыдущую оценку

    try {
      // Важно: ваш FastAPI бэкенд запущен на localhost:8000
      const response = await fetch(`http://localhost:8000/estimate?address=${encodeURIComponent(address)}`);

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

  return (
    <div className="App" style={{ textAlign: 'center', padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Real Estate Valuation MVP</h1>
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Введите адрес (например, 123 Main St)"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          style={{ padding: '10px', width: '300px', marginRight: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
        />
        <button
          onClick={fetchEstimate}
          disabled={loading || !address}
          style={{ padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
        >
          {loading ? 'Оцениваем...' : 'Получить оценку'}
        </button>
      </div>

      {error && <p style={{ color: 'red' }}>Ошибка: {error}</p>}

      {estimate && (
        <div style={{ border: '1px solid #eee', padding: '20px', borderRadius: '8px', maxWidth: '400px', margin: '20px auto', backgroundColor: '#f9f9f9' }}>
          <h2>Результат оценки:</h2>
          <p><strong>Адрес:</strong> {estimate.address}</p>
          <p><strong>Оценка:</strong> {estimate.estimated_value} {estimate.currency}</p>
          <p><strong>Дата оценки:</strong> {estimate.created_at ? new Date(estimate.created_at).toLocaleString() : 'N/A'}</p>
        </div>
      )}
    </div>
  );
}

export default App;