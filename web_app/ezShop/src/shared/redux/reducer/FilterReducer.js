const initialState = {
    priceFrom: null,
    priceBefore: null,
    sortType: "none",
    categories: []
};


const filterReducer = (state = initialState, action) => {
    switch (action.type) {
      case 'SET_FILTER':
        return {
          ...state,
          filter: action.payload
        };
      default:
        return state;
    }
};


export default filterReducer;






