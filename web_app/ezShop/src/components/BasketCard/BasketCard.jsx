import styles from './BasketCard.module.scss';
import { useTranslation } from 'react-i18next';
import filter_icon from '../../shared/icon/filter-icon.svg';
import search_icon from '../../shared/icon/search-icon.svg';
import snikers from '../../shared/images/temp/snikers.png'
import { useDispatch, useSelector } from 'react-redux';
import { setProductList } from '../../shared/redux/action/ProductListAction';
import { useEffect, useState } from 'react';


function BasketCard(props) {

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const [imgUrl, setImgUrl] = useState('');
    const appOptions = useSelector(state => state.appOptions.data);


    useEffect(() => {
    const url = `https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/files/get_file/${props.product.pictures[0]}`;
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
            return response.blob();
        })
        .then(blob => {
            const url = URL.createObjectURL(blob);
            setImgUrl(url)
        })
        .catch(error => {
            console.error('Error:', error);
        });

    }, [])


    function updateBuyCount(type) {
        let newProductList = productList.map(product => {
            if (product.id === props.product.id) {
                if(type == "plus"){
                return {
                    ...product,
                    buyCount: product.buyCount + 1
                };
            }else{
                return {
                    ...product,
                    buyCount: product.buyCount == 0 ? product.buyCount : product.buyCount - 1
                };
            }
            }
            return product;
        });

        dispatch(setProductList(newProductList))
    }


    return (
        <>
        <div className={styles.basket_card}>
            <img className={styles.image} src={imgUrl}></img>

            <div className={styles.right_container}>

                <div className={styles.top_info_container}>
                    <p className={styles.name}>{props.product.name}</p>
                    <p className={styles.price}>{props.product.price} {appOptions.currency_symbol}</p>
                </div>

                <div className={styles.counter}>
                    <p className={styles.minus_btn} onClick={() => updateBuyCount("minus")}>-</p>
                    <p className={styles.count}>{props.product.buyCount}</p>
                    <p className={styles.plus_btn} onClick={() => updateBuyCount("plus")}>+</p>
                </div>

            </div>

        </div>

        <div className={styles.separator}></div>
        </>
    );

}

export default BasketCard;