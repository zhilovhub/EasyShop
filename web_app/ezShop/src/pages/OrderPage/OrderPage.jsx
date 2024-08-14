import styles from './OrderPage.module.scss';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from "react-router-dom";
import order_img from "../../shared/images/order-img.svg"
import { useEffect, useState } from 'react';
import { use } from 'i18next';
import drop_down_icon from '../../shared/icon/drop-down-icon.svg'
import { initBackButton } from '@telegram-apps/sdk';
import TextInput from '../../components/inputs/TextInput/TextInput';
import { setIsCorrect } from '../../shared/redux/action/ValidateAction';


function OrderPage(){

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const botId = useSelector(state => state.botId.botId);
    const navigate = useNavigate();
    const [orderOptions, setOrderOptions] = useState([]);
    const [isCheck, setIsCheck] = useState(false)
    const isCorrect = useSelector(state => state.validate.isCorrect);

    const [backButton] = initBackButton();
    backButton.show();
    backButton.on('click', () => {
        navigate("/app/basket");
    });


    useEffect(() => {

        alert(botId)


        const url = `https://ezbots.ru:1537/api/settings/get_order_options/110`;
        fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'authorization-data': 'DEBUG'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            setOrderOptions(data)
            console.log(data)
        })
        .catch(error => {
            console.error('Error:', error);
        });


    }, []);


    function getOption(type, data){
        switch (type){
            case "text":
                return <TextInput isCheck={isCheck} data={data}></TextInput>
                
                // <>
                // <p className={styles.input_title}>{data.option.option_name}</p>
                // <input 
                // className={styles.input} 
                // placeholder={data.option.hint} 
                // style={ isCheck && data.option.required ? {border: "2px solid red"} : {}}>
                // </input>
                // </>
            case "choose":
                return <>
                <p className={styles.input_title}>{data.option.option_name}</p>
                <div className={styles.choose_container}>
                <select className={styles.input}>
                    <option value="1">На адрес</option>
                    <option value="2">Почта России</option>
                    <option value="3">СДЭК</option>
                    <option value="4">Boxberry</option>
                </select>
                <img className={styles.choose_icon} src={drop_down_icon}></img>
                </div>
                </>
            case "textarea":
                return <>
                <p className={styles.input_title}>{data.option.option_name}</p>
                <textarea 
                className={styles.textarea}
                placeholder={data.option.hint}
                style={ isCheck && data.option.required ? {border: "2px solid red"} : {}}
                ></textarea>
                </>
            default:
                <></>
        }
    }

    function filterByBuyCount() {
        return productList.filter(product => product.buyCount !== 0);
    }

    function orderSum() {
        return productList.reduce((total, item) => total + (item.buyCount * item.price || 0), 0);
    }

    function sendOrder(){

        setIsCheck(true);


        if(isCorrect == false){
            alert("Вы заполнили не все поля");
        }else if (isCorrect == true){

            const data = {
                bot_id: botId,
                raw_items: [],
                ordered_at: "2024-07-16T10:38:42.329Z",




            }

            const url = `https://ezbots.ru:1537/api/products/get_all_products?bot_id=${botId}`;
            const body = JSON.stringify([]);
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'authorization-data': 'DEBUG'
                },
                body: body
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
            })
            .catch(error => {
                console.error('Error:', error);
            });



        }

        dispatch(setIsCorrect(null))

    }

    return (
        <div className={styles.main_content_scroll}>
        <div className={styles.main_content}>

        <div className={styles.header}>
            <p className={styles.title}>{t('order__order')}</p>
        </div>

        <div className={styles.order_info}>
            <img className={styles.order_img} src={order_img}></img>
            <div className={styles.right_container}>
                <p className={styles.your_order_title}>{t('order__your_order')}</p>
                
                {filterByBuyCount().map(product => (
                    <p className={styles.product_name}>{product.name} {product.buyCount != 1 ? <>(x{product.buyCount})</> : <></>}</p>
                ))}

                <p className={styles.sum}>{orderSum()} ₽</p>
            </div>
        </div>

        <div className={styles.separator}></div>

        {orderOptions.map(option => 
            getOption(option.option.option_type, option)
        )}


        </div>

        <div className={styles.bottom_btn} onClick={sendOrder}>Отправить</div>
        </div>
    )

}

export default OrderPage;