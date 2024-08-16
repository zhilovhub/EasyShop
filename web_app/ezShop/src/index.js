import React, { Suspense } from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './app/18n.js';
import App from './app/App';
import Catalog from './pages/Catalog/Сatalog';
import { Routes, Route } from 'react-router-dom';
import { BrowserRouter } from 'react-router-dom';
import { Navigate } from 'react-router-dom';
// import { SDKProvider } from '@telegram-apps/sdk-react';
import { Provider } from 'react-redux';
import store from './shared/redux/store/ConfigureStore.js';
import BasketPage from './pages/BasketPage/BasketPage.jsx';
import OrderPage from './pages/OrderPage/OrderPage.jsx';
import FilterPage from './pages/FilterPage/FilterPage.jsx';
import ProductPage from './pages/ProductPage/ProductPage.jsx';
import { SDKProvider } from '@telegram-apps/sdk-react';
import { initMainButton } from '@telegram-apps/sdk';


const root = ReactDOM.createRoot(document.getElementById('root'));

const [mainButton] = initMainButton();

root.render(
  <SDKProvider acceptCustomStyles debug>
  <Provider store={store}>
  <Suspense fallback={<div>Loading...</div>}>
    <BrowserRouter>
      <Routes>
        <Route path="app" element={<App/>}>
          <Route path="catalog" element={<Catalog mainButton={mainButton}/>}></Route>
          <Route path="basket" element={<BasketPage/>}></Route>
          <Route path="order" element={<OrderPage/>}></Route>
          <Route path="filter" element={<FilterPage/>}></Route>
          <Route path="product" element={<ProductPage/>}></Route>
        </Route>
        <Route path="/" element={<Navigate to="/app/catalog" replace={true}/>}></Route>
      </Routes>
    </BrowserRouter>
    </Suspense>
  </Provider>
  </SDKProvider>
);


// const root = document.getElementById('root');
// ReactDOM.render(
//   <Provider store={store}>
//     <Suspense fallback={<div>Loading...</div>}>
//     <BrowserRouter>

//       <Routes>
//         <Route path="app" element={<App/>}>
//           <Route path="catalog" element={<Catalog/>}></Route>
//           <Route path="aboutshop" element={<AboutShop/>}></Route>
//         </Route>
//         <Route path="/" element={<Navigate to="/app/catalog" replace={true}/>}></Route>
//       </Routes>

//     </BrowserRouter>
//     </Suspense>
//   </Provider>,
//   root
// );

// const root = document.getElementById('root');
// ReactDOM.render(
//   <Provider store={store}>
//     <Suspense fallback={<div>Loading...</div>}>
//     <BrowserRouter>

//     <Routes>
//       <Route path="app" element={<App/>}>
//         <Route path="catalog" element={<Catalog/>}></Route>
//         <Route path="aboutshop" element={<AboutShop/>}></Route>
//       </Route>
//       <Route path="/" element={<Navigate to="/app/catalog" replace={true}/>}></Route>
//     </Routes>

//     </BrowserRouter>
//     </Suspense>
//   </Provider>,
//   root
// );