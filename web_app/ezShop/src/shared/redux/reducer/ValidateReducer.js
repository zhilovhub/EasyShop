const initialState = {
    isCorrect: null
};


const validateReducer = (state = initialState, action) => {
    switch (action.type) {
      case 'SET_VALIDATE':
        return {
          ...state,
          isCorrect: action.payload
        };
      default:
        return state;
    }
};


export default validateReducer;






