import { createStore, combineReducers } from 'redux';
import languageReducer from '../reducer/LangReducer';
import productListReducer from '../reducer/ProductListReducer';
import filterReducer from '../reducer/FilterReducer';
import validateReducer from '../reducer/ValidateReducer';
import botIdReducer from '../reducer/BotIdReducer';
import orderDataReducer from '../reducer/OrderDataReducer';
import appOptionReducer from '../reducer/AppOptionsReducer';
import categoriesReducer from '../reducer/CategoriesReducer';


const rootReducer = combineReducers({

  language: languageReducer,
  productList: productListReducer,
  filter: filterReducer,
  validate: validateReducer,
  botId: botIdReducer,
  orderData: orderDataReducer,
  appOptions: appOptionReducer,
  categories: categoriesReducer

});


const store = createStore(rootReducer);


export default store;