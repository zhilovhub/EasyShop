import { useState } from 'react';
import styles from './TextInput.module.scss';

function TextInput({isCheck, data}) {

    const [inputValue, setInputValue] = useState('');

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