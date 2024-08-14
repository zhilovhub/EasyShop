import { createStore, combineReducers } from 'redux';
import languageReducer from '../reducer/LangReducer';
import productListReducer from '../reducer/ProductListReducer';
import filterReducer from '../reducer/FilterReducer';
import validateReducer from '../reducer/ValidateReducer';

const rootReducer = combineReducers({
  language: languageReducer,
  productList: productListReducer,
  filter: filterReducer,
  validate: validateReducer
});

const store = createStore(rootReducer);


export default store;


















