import styles from './ProductPage.module.scss';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from "react-router-dom";
import snikers from '../../shared/images/temp/snikers.png'
import DropDownCard from '../../components/ProductPageOption/DropDownCard/DropDownCard';
import { useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { setProductList } from '../../shared/redux/action/ProductListAction';
import TextOption from '../../components/ProductPageOption/TextOption/TextOption'
import BlockOption from '../../components/ProductPageOption/BlockOption/BlockOption';
import PricedBlockOption from '../../components/ProductPageOption/PricedBlockOption/PricedBlockOption';
import Slider from '../../components/Slider/Slider';
import { initBackButton } from '@telegram-apps/sdk';


function ProductPage({mainButton}){

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const navigate = useNavigate();
    const location = useLocation();
    const { product } = location.state || {};
    const [imgUrl, setImgUrl] = useState('')
    const [currentProduct, setCurentProduct] = useState({})
    const [extraOptions, setExtraOptions] = useState([])
    const [productImages, setProductImages] = useState([])
    const [isImageLoad, setIsImageLoad] = useState(false)

    const [backButton] = initBackButton();
    backButton.show();
    backButton.on('click', () => {
        navigate("/app/catalog");
    });

    if(!isImageLoad){
        getImages();
        setIsImageLoad(true);
    }

    function getImages(){

    product.pictures.map(image => {
    const url = `https://ezbots.ru:1537/api/files/get_file/${image}`;
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
            setProductImages((arr) => [...arr, url])
        })
        .catch(error => {
            console.error('Error:', error);
        });
    })



    }

    useEffect(() => {

        mainButton
        .setBgColor("#9edcff")
        .setTextColor('#0C0C0C')
        .enable();

        mainButton
        .setText("В корзину")
        .show()
        .on('click', () => {
             updateBuyCount("plus")
        });

    }, [])


    useEffect(() => {

    // const currentUrl = window.location.href;
    // const myUrl = new URL(currentUrl);
    // let botId = myUrl.searchParams.get('bot_id');
    // if(!botId){
    //     botId = 110;
    // }

    productList.map(productItem => {
        console.log("id-1: " + productItem.id)
        console.log("id-2: " + product.id)
        if (productItem.id == product.id) {
            setCurentProduct(productItem)
            // setExtraOptions(productItem.extra_options)
            // setExtraOptions([{
            //     name: productItem.name,
            //     variants: [productItem.extra_options] // Копируем массив и добавляем новый элемент
            //   }]);
            setExtraOptions( 
                productItem.extra_options.map(option => {
                    return {
                        name: option.name,
                        type: option.type,
                        variants: option.variants,
                        variants_prices: option.variants_prices
                    }
                })
            );

            console.log("OPTIONS")
            console.log(extraOptions)
        }
    });
        
    }, [productList]);

    
    function updateBuyCount(type) {
        let newProductList = productList.map(productItem => {
            console.log(currentProduct.id == productItem.id)

            if (currentProduct.id == productItem.id) {
                if(type == "plus"){
                return {
                    ...currentProduct,
                    buyCount: productItem.buyCount == currentProduct.count ? productItem.buyCount : productItem.buyCount + 1
                };
            }else{
                return {
                    ...currentProduct,
                    buyCount: productItem.buyCount == 0 ? 0 : productItem.buyCount - 1
                };
            }
            }
            return productItem;

        });

        dispatch(setProductList(newProductList))
    }

    // function getCurrentProduct() {
    //     productList.map(productItem => {
    //         console.log("id-1: " + productItem.id)
    //         console.log("id-2: " + product.id)
    //         if (productItem.id == product.id) {
    //             console.log("Продукт " + productItem);
    //             return productItem;
    //         }
    //     });
    // }

    function getOption(type, data){
        switch (type){
            case "text":
                return <TextOption data={data}></TextOption>
            case "block":
                return <BlockOption data={data}></BlockOption>
            case "priced_block":
                return <PricedBlockOption data={data}></PricedBlockOption>
            default:
                <></>
        }
    }




    return (
        <div className={styles.main_content}>

        <div className={styles.content_scroll}>
             <div className={styles.content}>

                {/* <img className={styles.img} src={imgUrl}></img> */}
                <Slider urls={productImages}></Slider>
                <p className={styles.name}>{product.name}</p>
                <p className={styles.price}>{product.price} ₽</p>

                <div className={styles.product_blocks}>

                    {currentProduct.description != "" ? <TextOption data={{name: "Описание", variants: [currentProduct.description], variants_prices: [currentProduct.variants_prices]}}></TextOption> : <></>}

                    {extraOptions.map(option => getOption(option.type, option))}

                </div>

             </div>
        </div>

        <div className={styles.bottom_btn_container}>
            {currentProduct.buyCount != 0 ?
                <>
                    <div className={styles.bottom_btn} onClick={() => navigate("/app/basket")}>В корзине</div>
                    <p className={styles.bottom_count_minus} onClick={() => updateBuyCount("minus")}>-</p>
                    <p className={styles.bottom_count_value}>{currentProduct.buyCount}</p>
                    <p className={styles.bottom_count_plus} onClick={() => updateBuyCount("plus")}>+</p>
                </>
            : 
            <div className={styles.bottom_btn} onClick={() => updateBuyCount("plus")}>В корзину</div>
            }
        </div>

        </div>
    )

    
}

export default ProductPage;