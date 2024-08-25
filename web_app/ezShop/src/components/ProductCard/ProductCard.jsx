import styles from './ProductCard.module.scss';
import { useTranslation } from 'react-i18next';
import filter_icon from '../../shared/icon/filter-icon.svg';
import search_icon from '../../shared/icon/search-icon.svg';

// import minus_icon from '../../shared/icon/minus-icon.svg';
// import plus_icon from '../../shared/icon/plus-icon.svg';

import {ReactComponent as MinusIcon} from '../../shared/icon/minus-icon.svg';
import {ReactComponent as PlusIcon} from '../../shared/icon/plus-icon.svg';

import { useDispatch, useSelector } from 'react-redux';
import { setProductList } from '../../shared/redux/action/ProductListAction';
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from 'react';

function ProductCard(props) {

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const navigate = useNavigate();
    const [imgUrl, setImgUrl] = useState('')
    const [imgUrlIsLoad, setImgUrlIsLoad] = useState(false)
    const appOptions = useSelector(state => state.appOptions.data);
    
    useEffect(() => {

    // if(!imgUrlIsLoad){
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
        setImgUrlIsLoad(true)
    // }

    }, [props.product])




    function getButton(){
        if (props.product.buyCount == 0){
            return <div className={styles.button} onClick={(event) => {event.stopPropagation(); updateBuyCount("plus");}}>Купить</div>
        }else{
            return (
            <div className={styles.button_container}>
                <div className={styles.minus_btn} onClick={(event) => {event.stopPropagation(); event.preventDefault(); updateBuyCount("minus");}}>
                    {/* <img className={styles.btn_icon} src={minus_icon}></img> */}
                    <MinusIcon className={styles.btn_icon}></MinusIcon>
                </div>
                <div className={styles.plus_btn} onClick={(event) => {event.stopPropagation(); event.preventDefault(); updateBuyCount("plus");}}>
                    {/* <img className={styles.btn_icon} src={plus_icon}></img> */}
                    <PlusIcon className={styles.btn_icon}></PlusIcon>
                </div>
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
                    buyCount: product.buyCount + 1
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
            <p className={styles.price}>{props.product.price} {appOptions ? appOptions.currency_symbol : ""}</p>
            <p className={styles.name}>{props.product.name}</p>
            {getButton()}
        </div>
    );

}

export default ProductCard;