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
    backButton.on('click', backButtonListener, true);

    if(!isImageLoad){
        getImages();
        setIsImageLoad(true);
    }

    function getImages(){

    product.pictures.map(image => {
    const url = `https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/files/get_file/${image}`;
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

        console.log("New listener for mainButton is set")
        mainButton
        .setBgColor("#9edcff")
        .setTextColor('#0C0C0C')
        .enable()
        .setText("В корзину")
        .show()
        .on('click', mainButtonListener, true);

        return () => {
            mainButton.off('click', mainButtonListener);
            backButton.off('click', backButtonListener);
        }
    }, [productList])


    useEffect(() => {

    // const currentUrl = window.location.href;
    // const myUrl = new URL(currentUrl);
    // let botId = myUrl.searchParams.get('bot_id');
    // if(!botId){
    //     botId = 110;
    // }

    productList.forEach(productItem => {
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
                        variants_prices: option.variants_prices,
                        variantsIsSelected: option.variantsIsSelected ? option.variantsIsSelected : option.variants.map(variant => {return false}),
                        productId: productItem.id
                    }
                })
            );

            console.log("OPTIONS")
            console.log(extraOptions)
        }
    });
        
    }, [productList]);


    function mainButtonListener() {
        updateBuyCount("plus");
        navigate("/app/catalog");
    }

    function backButtonListener() {
        navigate("/app/catalog");
    }

    function getPrice(){

        let productForPrice;
        let price = null;

        productList.map(productItem => {
            if(product.id == productItem.id){
                productForPrice = productItem;
                return;
            }
        })

        productForPrice.extra_options.map(extraOption => {
            if (extraOption.type == "priced_block"){
                if(extraOption.variantsIsSelected){
                    extraOption.variantsIsSelected.map((item, index) => {
                        if(item == true){
                            price = extraOption.variants_prices[index];
                        }
                    })
                }
            }
        })

        if(price){
            return price;
        }else{
            return productForPrice.price;
        }
        
    }

    
    function updateBuyCount(type) {
        let newProductList = productList.map(productItem => {
            if (product.id == productItem.id) {
                if(type == "plus"){
                return {
                    ...productItem,
                    buyCount: productItem.buyCount == currentProduct.count ? productItem.buyCount : productItem.buyCount + 1
                };
            }else{
                return {
                    ...productItem,
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
                <p className={styles.price}>{getPrice()} ₽</p>

                <div className={styles.product_blocks}>

                    {product.description != "" ? <TextOption data={{name: "Описание", variants: [product.description], variants_prices: [product.variants_prices]}}></TextOption> : <></>}

                    {extraOptions.map(option => getOption(option.type, option))}

                </div>

             </div>
        </div>

        <div className={styles.bottom_btn_container}>
            {/* {currentProduct.buyCount != 0 ?
                <>
                    <div className={styles.bottom_btn} onClick={() => navigate("/app/basket")}>В корзине</div>
                    <p className={styles.bottom_count_minus} onClick={() => updateBuyCount("minus")}>-</p>
                    <p className={styles.bottom_count_value}>{currentProduct.buyCount}</p>
                    <p className={styles.bottom_count_plus} onClick={() => updateBuyCount("plus")}>+</p>
                </>
            : 
            <div className={styles.bottom_btn} onClick={() => updateBuyCount("plus")}>В корзину</div>
            } */}
        </div>

        </div>
    )

    
}

export default ProductPage;