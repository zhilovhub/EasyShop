const initialState = {
    data: null
};


const appOptionReducer = (state = initialState, action) => {
    switch (action.type) {
      case 'SET_OPTION':
        return {
          ...state,
          data: action.payload
        };
      default:
        return state;
    }
};


export default appOptionReducer;






