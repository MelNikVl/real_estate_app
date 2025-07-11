import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Get Estimate button', () => {
  render(<App />);
  const buttonElement = screen.getByText(/get estimate/i);
  expect(buttonElement).toBeInTheDocument();
});
