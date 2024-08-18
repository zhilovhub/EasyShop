import styles from './App.module.scss';
import { Outlet } from 'react-router';
import { useSelector } from 'react-redux';
import { useEffect } from 'react';

function App() {

  return (
    <div className="app">
      <Outlet/>
    </div>
  );
}

export default App;
