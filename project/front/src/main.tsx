import React from 'react';
import ReactDOM from 'react-dom/client';
import { DSFRConfig } from "@dataesr/dsfr-plus"
import { BrowserRouter } from 'react-router-dom';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import Router from './router';
import './styles/index.scss';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <DSFRConfig>
      <BrowserRouter>
        <QueryClientProvider client={queryClient}>
          <ReactQueryDevtools />
          <Router />
        </QueryClientProvider>
      </BrowserRouter>
    </DSFRConfig>
  </React.StrictMode>
)
