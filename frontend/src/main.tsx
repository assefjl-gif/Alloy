import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './design-system/tokens.css';
import './design-system/base.css';
import './design-system/components.css';
import './styles/app.css';
import './styles/print.css';
import { App } from './app/App.tsx';
import { boot } from './app/boot.ts';

boot();

const el = document.getElementById('root');
if (!el) throw new Error('#root ausente');
createRoot(el).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
