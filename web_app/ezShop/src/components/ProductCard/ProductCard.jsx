import styles from './ProductCard.module.scss';
import { useTranslation } from 'react-i18next';
import filter_icon from '../../shared/icon/filter-icon.svg';
import search_icon from '../../shared/icon/search-icon.svg';
import snikers from '../../shared/images/temp/snikers.png'
import { useDispatch, useSelector } from 'react-redux';
import { setProductList } from '../../shared/redux/action/ProductListAction';
import { useNavigate } from "react-router-dom";
import { useState } from 'react';

function ProductCard(props) {

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const navigate = useNavigate();
    const [imgUrl, setImgUrl] = useState('')

    const url = `https://ezbots.ru:2024/api/files/get_file/${props.product.pictures[0]}`;
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







    function getButton(){
        if (props.product.buyCount == 0){
            return <div className={styles.button} onClick={(event) => {event.stopPropagation(); updateBuyCount("plus");}}>Купить</div>
        }else{
            return (
            <div className={styles.button_container}>
                <div className={styles.minus_btn} onClick={(event) => {event.stopPropagation(); updateBuyCount("minus");}}>-</div>
                <div className={styles.plus_btn} onClick={(event) => {event.stopPropagation(); updateBuyCount("plus");}}>+</div>
            </div>
            )
        }
    }


    function updateBuyCount(type) {
        let newProductList = productList.map(product => {
            if (product.id === props.product.id) {
                if(type == "plus"){
                return {
                    ...product,
                    buyCount: product.buyCount == product.count ? product.buyCount : product.buyCount + 1
                };
            }else{
                return {
                    ...product,
                    buyCount: product.buyCount - 1
                };
            }
            }
            return product;
        });

        dispatch(setProductList(newProductList))
    }

    const product = props.product;

    return (
        <div className={styles.product_card} onClick={() => navigate("/app/product", { state: { product }, imgUrl: {imgUrl} })}>
            {props.product.buyCount != 0 ? <p className={styles.buyCount}>{props.product.buyCount}</p> : <></>}
            <img className={styles.image} src={imgUrl}></img>
            <p className={styles.price}>{props.product.price} ₽</p>
            <p className={styles.name}>{props.product.name}</p>
            {getButton()}
        </div>
    );

}

export default ProductCard;