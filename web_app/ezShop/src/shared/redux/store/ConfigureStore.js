import { createStore, combineReducers } from 'redux';
import languageReducer from '../reducer/LangReducer';
import productListReducer from '../reducer/ProductListReducer';
import filterReducer from '../reducer/FilterReducer';

const rootReducer = combineReducers({
  language: languageReducer,
  productList: productListReducer,
  filter: filterReducer
});

const store = createStore(rootReducer);


export default store;


















