import { useEffect, useState } from 'react';
import styles from './ChooseInput.module.scss';
import { setIsCorrect } from '../../../shared/redux/action/ValidateAction';
import { useDispatch, useSelector } from 'react-redux';
import { setOrderData, setOrderItem } from '../../../shared/redux/action/OrderDataAction';
// import drop_down_icon from '../../../shared/icon/drop-down-icon.svg';
import {ReactComponent as DropDownIcon} from '../../../shared/icon/drop-down-icon.svg';


function ChooseInput({isCheck, data}) {

    const [inputValue, setInputValue] = useState('');
    const dispatch = useDispatch();
    const isCorrect = useSelector(state => state.validate.isCorrect);
    const orderData = useSelector(state => state.orderData.orderData);

    useEffect(() => {

      setInputValue("На адрес")

    }, [])

    useEffect(() => {
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
      <div className={styles.choose_container}>
      <select className={styles.input}
      onChange={(event) => setInputValue(event.target.value)}>
          <option value="На адрес">На адрес</option>
          <option value="Почта России">Почта России</option>
          <option value="СДЭК">СДЭК</option>
          <option value="Boxberry">Boxberry</option>
      </select>
      <DropDownIcon className={styles.choose_icon}></DropDownIcon>
      {/* <img className={styles.choose_icon} src={drop_down_icon}></img> */}
      </div>
      </>
    );

}

export default ChooseInput;