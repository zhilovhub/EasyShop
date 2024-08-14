import styles from './OrderPage.module.scss';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from "react-router-dom";
import order_img from "../../shared/images/order-img.svg"
import { useEffect, useState } from 'react';
import { use } from 'i18next';
import drop_down_icon from '../../shared/icon/drop-down-icon.svg'


function OrderPage(){

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const navigate = useNavigate();
    const [orderOptions, setOrderOptions] = useState([]);


    useEffect(() => {


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
                return <>
                <p className={styles.input_title}>{data.option.option_name}</p>
                <input className={styles.input} placeholder={data.option.hint}></input>
                </>
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
                <textarea className={styles.textarea} placeholder={data.option.hint}></textarea>
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

        let optionList = document.getElementsByClassName("")
        orderOptions.map(option => {

        })
        

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
            // <>
            // <p className={styles.input_title}>{option.option.option_name}</p>
            // <input className={styles.input} placeholder={option.option.hint}></input>
            // </>
            getOption(option.option.option_type, option)
        )}


        </div>

        <div className={styles.bottom_btn} onClick={sendOrder}>Отправить</div>
        </div>
    )

}

export default OrderPage;