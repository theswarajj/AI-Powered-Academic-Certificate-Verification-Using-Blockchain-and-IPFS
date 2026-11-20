import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#FFFFFF',
              color: '#111827',
              border: '1px solid #E5E7EB',
              borderRadius: '12px',
              boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
              fontWeight: 500,
              fontSize: '14px',
            },
            success: {
              iconTheme: {
                primary: '#059669',
                secondary: '#FFFFFF',
              },
            },
            error: {
              iconTheme: {
                primary: '#DC2626',
                secondary: '#FFFFFF',
              },
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
)
