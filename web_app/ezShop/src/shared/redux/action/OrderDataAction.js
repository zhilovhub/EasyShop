

export const setOrderData = (orderData) => {
    return {
      type: 'SET_ORDER_DATA',
      payload: orderData
    };
};

export const setOrderItem = (fieldName, value) => {
  return {
    type: 'SET_ORDER_ITEM',
    payload: {fieldName: fieldName, value: value}
  };
};









