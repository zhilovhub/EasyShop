import styles from './App.module.scss';
import { Outlet } from 'react-router';
// import eruda from 'eruda'

function App() {
  // eruda.init()
  return (
    <div className="app">
      <Outlet/>
    </div>
  );
}

export default App;
