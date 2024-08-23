import styles from './OrderPage.module.scss';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from "react-router-dom";
// import order_img from "../../shared/images/order-img.svg";
import {ReactComponent as OrderImg} from "../../shared/images/order-img.svg";
import { useEffect, useState } from 'react';
import { use } from 'i18next';
import drop_down_icon from '../../shared/icon/drop-down-icon.svg'
import { initBackButton } from '@telegram-apps/sdk';
import TextInput from '../../components/inputs/TextInput/TextInput';
import { setIsCorrect } from '../../shared/redux/action/ValidateAction';
import { retrieveLaunchParams } from '@telegram-apps/sdk';
import { initDataRaw } from '@telegram-apps/sdk';
import { TelegramClient, Button } from '@telegram-apps/sdk';
import { initMiniApp } from '@telegram-apps/sdk';
import { initMainButton } from '@telegram-apps/sdk';
import { setOrderData } from '../../shared/redux/action/OrderDataAction';
import TextAreaInput from '../../components/inputs/TextAreaInput/TextAreaInput';
import ChooseInput from '../../components/inputs/ChooseInput/ChooseInput';
import { initInvoice } from '@telegram-apps/sdk';
import { initPopup } from '@telegram-apps/sdk';


function OrderPage({mainButton}){

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const orderData = useSelector(state => state.orderData.orderData);
    const botId = useSelector(state => state.botId.botId);
    const navigate = useNavigate();
    const [orderOptions, setOrderOptions] = useState([]);
    const [isCheck, setIsCheck] = useState(false)
    const isCorrect = useSelector(state => state.validate.isCorrect);
    const appOptions = useSelector(state => state.appOptions.data);

    const [rawOrderOptions, setRawOrderOptions] = useState({});

    const {initData} = retrieveLaunchParams();
    const { initDataRaw } = retrieveLaunchParams();
    const popup = initPopup();
    const [miniApp] = initMiniApp();

    function mainButtonListener() {
        sendOrder();
        mainButton.off('click', mainButtonListener);
    }
    
    
    function backButtonListener() {
        navigate("/app/basket");
    }

    useEffect(() => {
        const [backButton] = initBackButton();
        backButton.show();
        backButton.on('click', backButtonListener, true);

        mainButton
            .setText("Отправить")
            .setBgColor("#9edcff")
            .setTextColor('#0C0C0C')
            .enable()
            .show()

        // const url = `https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/settings/get_order_options/${botId}`;
        // fetch(url, {
        //     method: 'GET',
        //     headers: {
        //         'Content-Type': 'application/json',
        //         'Accept': 'application/json',
        //         'authorization-data': 'DEBUG'
        //     }
        // })
        // .then(response => {
        //     if (!response.ok) {
        //         throw new Error('Network response was not ok ' + response.statusText);
        //     }
        //     return response.json();
        // })
        // .then(data => {
        //     // setOrderOptions(data)

        //     const newOrderData = data.map(orderItem => {
        //         orderItem.value = ""
        //         console.log("--------")
        //         console.log(orderItem.option_name)
        //         console.log("+++++++++")
        //         console.log(orderItem)
        //         return orderItem
        //     })

        //     console.log("newOrderData")
        //     // console.log(newOrderData)
        //     dispatch(setOrderData(data))

        //     console.log('initOrderData')
        //     console.log(data)
        //     console.log(orderData)
        // })
        // .catch(error => {
        //     console.error('Error:', error);
        // });

    
        return () => {
            backButton.off('click', backButtonListener)
        }

    }, []);



    useEffect(() => {
        
        console.log('Updated orderData:', orderData);
        console.log('Updated productList:', productList);

        mainButton.on('click', mainButtonListener, true);

        return () => {
            mainButton.off('click', mainButtonListener)
        }
    }, [orderData, productList]);




    function getOption(type, data){
        switch (type){
            case "text":
                return <TextInput isCheck={isCheck} data={data}></TextInput>
            case "choose":
                return <ChooseInput isCheck={isCheck} data={data}></ChooseInput>
            case "text_area":
                return <TextAreaInput isCheck={isCheck} data={data}></TextAreaInput>
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

    function checkRequired(){

        let status = true;

        orderData.map(orderItem => {
            console.log("Проверка")
            console.log(orderItem.value)
            console.log(orderItem.option.required)
            if(orderItem.value == '' && orderItem.option.required == true){
                status = false;
            }
        })

        return status;

    }

    function sendOrder(){

        setIsCheck(true);
        
        if(!checkRequired()){
            popup.open({message: 'Вы заполнили не все поля'})
        }else if (checkRequired()){

            const data = {
                bot_id: botId,
                raw_items: {},
                raw_order_options: {},
                ordered_at: new Date().toISOString(),
                from_user: initData.user.id,
            }

            console.log("---------")
            console.log(orderData)

            orderData.map(orderItem => {
                console.log("+++++++++++")
                console.log(orderItem)
                data.raw_order_options[orderItem.option.id] = orderItem.value
            })

            console.log("productList")
            console.log(productList)

            console.log("-------------------ГЕНЕРАЦИЯ ДАННЫХ-------------------")
            productList.map(orderItem => {
                if (orderItem.buyCount != 0){
                    console.log(orderItem);
                    data.raw_items[orderItem.id] = {
                        amount: orderItem.buyCount,
                        chosen_options: []
                    };
                        orderItem.extra_options.map(extraOption => {
                            if (extraOption.type == 'block' || extraOption.type == 'priced_block'){
                                if(extraOption.variantsIsSelected){
                                    extraOption.variantsIsSelected.map((variant, index) => {
                                        if(variant){
                                            const newOption = {
                                                name: extraOption.name,
                                                selected_variant: extraOption.variants[index]
                                            }
                                            data.raw_items[orderItem.id].chosen_options.push(newOption);
                                        }
                                    })
                                }
                        
                        }})
                    



                }
            })

            console.log("-------------------ДАННЫЕ ДЛЯ ОТПРАВКИ-------------------")
            console.log(data)

            const url = `https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/orders/send_order_data_to_bot`;
            const body = JSON.stringify(data);
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'authorization-data': initDataRaw
                },
                body: body
            })
            .then(response => {

                if (!response.ok) {
                    // alert('error')
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {


                const invoiceUrl = data.invoice_url


                if (invoiceUrl){
                    const invoice = initInvoice();

                    invoice
                    .open(invoiceUrl, 'url')
                    .then((status) => {
                      // Output: 'paid'
                      switch (status){
                        case 'paid':
                            popup.open({message: 'Оплата прошла успешно ✅'});
                            miniApp.close();
                            break;
                        case 'failed':
                            popup.open({message: 'Произошла ошибка при обработке платежа ❌\nОбратитесь к администратору'});
                            break;
                        case 'pending':
                            popup.open({message: 'Оплата прошла успешно ✅'});  // TODO make loading screen
                            miniApp.close();
                            break;
                        case 'cancelled':
                            popup.open({message: 'Оплата отменена ⚠️'});
                            break;
                      }
                    });


                }else{
                    miniApp.close();
                }

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
            {/* <img className={styles.order_img} src={order_img}></img> */}
            <OrderImg className={styles.order_img}></OrderImg>
            <div className={styles.right_container}>
                <p className={styles.your_order_title}>{t('order__your_order')}</p>
                
                {filterByBuyCount().map(product => (
                    <p className={styles.product_name}>{product.name} {product.buyCount != 1 ? <>(x{product.buyCount})</> : <></>}</p>
                ))}

                <p className={styles.sum}>{orderSum()} {appOptions.currency_symbol}</p>
            </div>
        </div>

        <div className={styles.separator}></div>

        {orderData.map(option => 
            getOption(option.option.option_type, option)
        )}

        </div>


        </div>
    )

}

export default OrderPage;