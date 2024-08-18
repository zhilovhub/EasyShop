const initialState = {
    botId: null
};


const botIdReducer = (state = initialState, action) => {
    switch (action.type) {
      case 'SET_BOTID':
        return {
          ...state,
          botId: action.payload
        };
      default:
        return state;
    }
};


export default botIdReducer;






