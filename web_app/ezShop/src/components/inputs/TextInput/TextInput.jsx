import { useEffect, useState } from 'react';
import styles from './TextInput.module.scss';
import { setIsCorrect } from '../../../shared/redux/action/ValidateAction';
import { useDispatch, useSelector } from 'react-redux';

function TextInput({isCheck, data}) {

    const [inputValue, setInputValue] = useState('');
    const dispatch = useDispatch();
    const isCorrect = useSelector(state => state.validate.isCorrect);

    useEffect(() => {

            if(inputValue != ''){
                if(isCorrect == null || isCorrect == true){
                dispatch(setIsCorrect(true))
                }
            }else{
                dispatch(setIsCorrect(false))
            }
        
    }, [inputValue])


    return (
        <>
            <p className={styles.input_title}>{data.option.option_name}</p>
            <input 
            className={styles.input} 
            placeholder={data.option.hint}
            onChange={(event) => setInputValue(event.target.value)}
            style={ isCheck && inputValue == '' && data.option.required ? {border: "1px solid red"} : {}}>
            </input>
        </>
    );

}

export default TextInput;