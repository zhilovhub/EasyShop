import styles from './App.module.scss';
import { Outlet } from 'react-router';
import { useSelector, useDispatch } from 'react-redux';
import { useEffect } from 'react';
import { setAppOption } from '../shared/redux/action/AppOptionsAction';
import { setOrderData } from '../shared/redux/action/OrderDataAction';
import { setCategories } from '../shared/redux/action/CategoriesAction';

function App() {

  const botId = useSelector(state => state.botId.botId);
  const dispatch = useDispatch();
  const appOptions = useSelector(state => state.appOptions.data);


  useEffect(() => {

    if(botId){

    const url = `https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/settings/get_web_app_options/${botId}`;

    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'authorization-data': 'DEBUG'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {

      dispatch(setAppOption(data))

    })
    .catch(error => {
        console.error('Error:', error);
    });



    fetch(`https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/settings/get_order_options/${botId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'authorization-data': 'DEBUG'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        dispatch(setOrderData(data))
    })
    .catch(error => {
        console.error('Error:', error);
    });



    fetch(`https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/categories/get_all_categories/${botId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'authorization-data': 'DEBUG'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
      dispatch(setCategories(data))
        
    })
    .catch(error => {
        console.error('Error:', error);
    });

    }
  }, [botId])

  return (
    <div className="app">
      <Outlet/>
    </div>
  );
}

export default App;
