// real_estate_app/frontend/src/App.js

import React, { useState, useEffect, useRef } from 'react';
import './App.css'; 

function App() {
  const [address, setAddress] = useState('');
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]); // Состояние для подсказок
  const [showSuggestions, setShowSuggestions] = useState(false); // Состояние для отображения списка подсказок

  // Используйте process.env.REACT_APP_GOOGLE_API_KEY для вашего ключа Google API
  // Убедитесь, что вы создали файл .env.development в папке frontend
  // с REACT_APP_GOOGLE_API_KEY=ВАШ_КЛЮЧ
  const GOOGLE_API_KEY = process.env.REACT_APP_GOOGLE_API_KEY; 

  // Реф для дебаунсинга запросов к Google API
  const debounceTimeoutRef = useRef(null);

  // URL вашего FastAPI бэкенда
  const BACKEND_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  // Функция для запроса оценки недвижимости с бэкенда (без изменений)
  const fetchEstimate = async (selectedAddress = address) => {
    if (!selectedAddress.trim()) {
      setError('Пожалуйста, введите адрес.');
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

  // Функция для получения автоподсказок от Google Places API
  const fetchSuggestions = async (input) => {
    if (!GOOGLE_API_KEY) {
      console.error("Google API Key is not set. Please set REACT_APP_GOOGLE_API_KEY in your .env file.");
      setSuggestions([]);
      return;
    }
    if (!input.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    try {
      // Endpoint для Places Autocomplete API
      const googlePlacesUrl = `https://maps.googleapis.com/maps/api/place/autocomplete/json?input=${encodeURIComponent(input)}&types=address&components=country:us&key=${GOOGLE_API_KEY}`;
      
      const response = await fetch(googlePlacesUrl);
      const data = await response.json();

      if (data.status === 'OK') {
        setSuggestions(data.predictions.map(prediction => prediction.description));
        setShowSuggestions(true);
      } else {
        console.error("Google Places API error:", data.status, data.error_message);
        setSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (err) {
      console.error("Error fetching Google Places suggestions:", err);
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Обработчик изменения поля ввода с дебаунсингом
  const handleAddressInputChange = (e) => {
    const input = e.target.value;
    setAddress(input);
    
    // Очищаем предыдущий таймаут
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    // Устанавливаем новый таймаут для вызова API
    debounceTimeoutRef.current = setTimeout(() => {
      fetchSuggestions(input);
    }, 300); // Задержка в 300 мс
  };

  // Обработчик выбора подсказки
  const handleSelectSuggestion = (selectedSuggestion) => {
    setAddress(selectedSuggestion); // Устанавливаем выбранный адрес в поле ввода
    setSuggestions([]); // Очищаем список подсказок
    setShowSuggestions(false); // Скрываем список
    // Можно сразу же запросить оценку для выбранного адреса
    // fetchEstimate(selectedSuggestion); 
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
    <div className="App" style={{ textAlign: 'center', padding: '20px', fontFamily: 'Arial, sans-serif', backgroundColor: '#f0f2f5', minHeight: '100vh', color: '#333' }}>
      <h1 style={{ color: '#2c3e50', marginBottom: '30px' }}>Real Estate Valuation MVP</h1>
      <div style={{ marginBottom: '30px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{ position: 'relative', width: '400px', maxWidth: 'calc(100% - 150px)' }}> {/* Обертка для позиционирования подсказок */}
          <input
            type="text"
            placeholder="Введите адрес (например, 5500 Grand Lake Dr, San Antonio, TX 78244)"
            value={address}
            onChange={handleAddressInputChange} // Используем новый обработчик
            onFocus={() => address.trim() && setSuggestions([]) && fetchSuggestions(address)} // Показываем подсказки при фокусе, если что-то уже введено
            onBlur={() => setTimeout(() => setShowSuggestions(false), 100)} // Скрываем подсказки с небольшой задержкой
            style={{ 
              padding: '12px 15px', 
              width: '100%', 
              marginRight: '15px', // Убрал, т.к. теперь в flex-col
              borderRadius: '8px', 
              border: '1px solid #a0a0a0', 
              boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.1)',
              fontSize: '16px',
              boxSizing: 'border-box' // Важно для правильной ширины
            }}
          />
          {showSuggestions && suggestions.length > 0 && (
            <ul style={{
              position: 'absolute',
              top: '100%', // Располагаем под полем ввода
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
              zIndex: 100 // Чтобы список был поверх других элементов
            }}>
              {suggestions.map((suggestion, index) => (
                <li 
                  key={index} 
                  onClick={() => handleSelectSuggestion(suggestion)}
                  style={{
                    padding: '10px 15px',
                    borderBottom: '1px solid #eee',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                >
                  {suggestion}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button
          onClick={() => fetchEstimate()} // Теперь вызываем оценку только по кнопке
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
            marginTop: '15px' // Отступ от поля ввода
          }}
        >
          {loading ? 'Оцениваем...' : 'Получить оценку'}
        </button>
      </div>

      {error && <p style={{ color: 'red', fontSize: '1.1em', marginTop: '20px' }}>Ошибка: {error}</p>}

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
          <h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>Результат оценки:</h2>
          <div style={{ textAlign: 'left', lineHeight: '1.8' }}>
            <p><strong>Адрес:</strong> {estimate.formattedAddress || estimate.address}</p>
            <p><strong>Оценка:</strong> {estimate.valuation ? `${estimate.valuation} ${estimate.currency}` : 'Нет данных'}</p>
            <p><strong>Тип недвижимости:</strong> {estimate.property_type || 'Нет данных'}</p>
            <p><strong>Спальни:</strong> {estimate.bedrooms || 'Нет данных'}</p>
            <p><strong>Ванные:</strong> {estimate.bathrooms || 'Нет данных'}</p>
            <p><strong>Площадь (кв.футов):</strong> {estimate.square_footage || 'Нет данных'}</p>
            <p><strong>Площадь участка (кв.футов):</strong> {estimate.lot_size || 'Нет данных'}</p>
            <p><strong>Год постройки:</strong> {estimate.year_built || 'Нет данных'}</p>
            <p><strong>Дата последней продажи:</strong> {estimate.last_sale_date ? new Date(estimate.last_sale_date).toLocaleDateString() : 'Нет данных'}</p>
            <p><strong>Дата оценки:</strong> {estimate.created_at ? new Date(estimate.created_at).toLocaleString() : 'N/A'}</p>

            {estimate.sale_history_json && Object.keys(parseSaleHistory(estimate.sale_history_json)).length > 0 && (
              <div style={{ marginTop: '20px', borderTop: '1px dashed #e0e0e0', paddingTop: '20px' }}>
                <h3 style={{ color: '#2c3e50', marginBottom: '15px' }}>История продаж объекта:</h3>
                <ul style={{ listStyleType: 'none', padding: 0 }}>
                  {Object.entries(parseSaleHistory(estimate.sale_history_json)).map(([dateKey, sale]) => (
                    <li key={dateKey} style={{ marginBottom: '10px', backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '5px' }}>
                      <strong>Событие:</strong> {sale.event || 'Sale'} <br />
                      <strong>Дата:</strong> {sale.date ? new Date(sale.date).toLocaleDateString() : 'N/A'} <br />
                      <strong>Цена:</strong> {sale.price ? `${sale.price} ${estimate.currency}` : 'N/A'}
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
