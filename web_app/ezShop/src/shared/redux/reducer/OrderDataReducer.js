const initialState = {
    orderData: []
};
  
  const orderDataReducer = (state = initialState, action) => {
    switch (action.type) {
      case 'SET_ORDER_DATA':
        return {
          ...state,
          orderData: action.payload
        };
      case 'SET_ORDER_ITEM':
        return {
          ...state,
          orderData: state.orderData.map(orderItem => {
            return 1
          })
        };
      default:
        return state;
    }
  };
  
  
  export default orderDataReducer;