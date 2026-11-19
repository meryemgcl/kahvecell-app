import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import OtpPage from './pages/OtpPage'
import RegisterPage from './pages/RegisterPage'
import ShopDetailPage from './pages/ShopDetailPage'
import OrderPage from './pages/OrderPage'
import QRPage from './pages/QRPage'
import SubscriptionPage from './pages/SubscriptionPage'
import HistoryPage from './pages/HistoryPage'
import { useAuthStore } from './store/authStore'
import ShopOwnerPage from './pages/ShopOwnerPage'
import ToastStack from './components/ToastStack'

function App() {
  const accessToken = useAuthStore((state) => state.accessToken)
  const role = useAuthStore((state) => state.role)

  return (
    <>
      <ToastStack />
      <Routes>
      <Route
        path="/"
        element={
          !accessToken
            ? <Navigate to="/login" replace />
            : role === 'SHOP_OWNER'
              ? <Navigate to="/shop-panel" replace />
              : <HomePage />
        }
      />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/otp" element={<OtpPage />} />
      <Route
        path="/shops/:shopId"
        element={accessToken ? <ShopDetailPage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/shops/:shopId/order/:productId"
        element={accessToken ? <OrderPage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/orders/:orderId/qr"
        element={accessToken ? <QRPage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/subscriptions"
        element={accessToken ? <SubscriptionPage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/history"
        element={accessToken ? <HistoryPage /> : <Navigate to="/login" replace />}
      />
      <Route
        path="/shop-panel"
        element={
          accessToken && role === 'SHOP_OWNER'
            ? <ShopOwnerPage />
            : <Navigate to="/" replace />
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default App
