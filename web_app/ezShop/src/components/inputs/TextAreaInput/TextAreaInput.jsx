import { useEffect, useState } from 'react';
import styles from './TextAreaInput.module.scss';
import { setIsCorrect } from '../../../shared/redux/action/ValidateAction';
import { useDispatch, useSelector } from 'react-redux';
import { setOrderData, setOrderItem } from '../../../shared/redux/action/OrderDataAction';

function TextAreaInput({isCheck, data}) {

    const [inputValue, setInputValue] = useState('');
    const dispatch = useDispatch();
    const isCorrect = useSelector(state => state.validate.isCorrect);
    const orderData = useSelector(state => state.orderData.orderData);

    useEffect(() => {

            // if(inputValue != ''){
            //     if(isCorrect == null){
            //         dispatch(setIsCorrect(true))
            //     }else if(isCorrect == true){
            //         dispatch(setIsCorrect(true))
            //     }
            // }else if(inputValue == ''){
            //     dispatch(setIsCorrect(false))
            // }

            // alert(data.option.option_name)

            const newOrderData = orderData.map(orderItem => {
                if (data.option.id == orderItem.option.id){
                  orderItem.value = inputValue
                }
                return orderItem
              })

              console.log(newOrderData)

            dispatch(setOrderData(newOrderData))
            console.log(orderData)
        
    }, [inputValue])


    return (
        <>
        <p className={styles.input_title}>{data.option.option_name}</p>
        <textarea 
        className={styles.textarea}
        placeholder={data.option.hint}
        onChange={(event) => setInputValue(event.target.value)}
        style={ isCheck && inputValue == '' && data.option.required ? {border: "1px solid rgb(249, 133, 133)"} : {}}>
        </textarea>
        </>
    );

}

export default TextAreaInput;