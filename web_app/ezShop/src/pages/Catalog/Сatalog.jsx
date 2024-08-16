import styles from './Сatalog.module.scss';
import { useTranslation } from 'react-i18next';
import filter_icon from '../../shared/icon/filter-icon.svg';
import search_icon from '../../shared/icon/search-icon.svg';
import empty_catalog_img from '../../shared/images/empty-catalog-img.svg';
import search_2_icon from '../../shared/icon/search-2-icon.svg';
import ProductCard from '../../components/ProductCard/ProductCard';
import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
// import { setProducts, getProducts } from '../../shared/redux/action/ProductsAction';
import { setLanguage } from '../../shared/redux/action/LangAction';
import { setProductList } from '../../shared/redux/action/ProductListAction';
import { useNavigate } from "react-router-dom";
import { useRef } from 'react';
import { initBackButton } from '@telegram-apps/sdk';
import { setBotId } from '../../shared/redux/action/BotIdAction';
import { initMainButton } from '@telegram-apps/sdk';



function Catalog() {

    console.log("useEffect");

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const botId = useSelector(state => state.botId.botId);
    const navigate = useNavigate();
    const [searchValue, setSearchValue] = useState('');
    const [products, setProducts] = useState([]);
    const inputRef = useRef(null);
    const filter = useSelector(state => state.filter);

    const [mainButton] = initMainButton();



    useEffect(() => {

        // TG API --START--

        const [backButton] = initBackButton();

        backButton.hide();

        // window.Telegram.WebApp.onEvent('mainButtonClicked', )
        const [mainButton] = initMainButton();
        
        mainButton
        .setText("Корзина")
        .setBgColor("#9edcff")
        .setTextColor('#0C0C0C')
        .on('click', () => {
                navigate("/app/basket");
        }, true);
        
        mainButton.show();
        mainButton.enable();
        
        
        // TG API --END--

        const currentUrl = window.location.href;
        const myUrl = new URL(currentUrl);
        let newBotId = myUrl.searchParams.get('bot_id');

        if(newBotId){
            dispatch(setBotId(newBotId))
        }
        // alert(botId)


        if (productList.length == 0){

        const url = `https://ezbots.ru:1537/api/products/get_all_products?bot_id=${newBotId}`;
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
            console.log("data");
            console.log(data);
            setCurrentProducts(data)
            setProducts(productList)
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }


    }, []);


    const focusInput = () => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      };


    function setCurrentProducts(data) {

        let curentProductsArr = []

        data.forEach((product) => {
            console.log("productData")
            let productData = {
                id: product.id,
                article: product.article,
                category: product.category,
                count: product.count,
                description: product.description,
                name: product.name,
                price: product.price,
                buyCount: 0,
                pictures: product.picture,
                extra_options: product.extra_options
            }
            console.log("Продукт")
            console.log(productData)
            curentProductsArr.push(productData)
        })

        dispatch(setProductList(curentProductsArr))
    }

    // products, searchText, sortKey, sortOrder, selectedCategories

    function filterAndSortArray() {

        let array = productList;
        let searchText = searchValue;
        let sortKey = 'price';
        let sortOrder = filter.sortType


        return array
            .filter(item => {
                // Фильтрация по тексту поиска
                return item.name.toLowerCase().includes(searchText.toLowerCase());
            })
            .filter(item => {
                // Фильтрация по выбранным категориям
                if(filter.categories.length == 0){
                    return true
                }else if(item.category == null){
                    return false
                }else{
                    return filter.categories.map(i => i.id).includes(item.category[0]);
                }
            })
            .filter(item => {
                // Фильтрация по тексту поиска
                return item.price >= (filter.priceFrom == null ? 0 : filter.priceFrom) && item.price <= (filter.priceBefore == null ? Infinity : filter.priceBefore);
            })
            .sort((a, b) => {
                if (sortOrder === 'По возрастанию') {
                    // Сортировка по возрастанию
                    return a[sortKey] > b[sortKey] ? 1 : -1;
                } else if (sortOrder === 'По убыванию') {
                    // Сортировка по убыванию
                    return a[sortKey] < b[sortKey] ? 1 : -1;
                }
                return 0; // Если порядок не указан, оставить порядок неизменным
            });
    }
    

    function sumBuyCount() {
        return productList.reduce((total, item) => total + (item.buyCount || 0), 0);
    }

    function getBottomButton(){
        if (sumBuyCount() == 0){

            // const [mainButton] = initMainButton();

            // mainButton
            // .setText("Начать оформление")
            // .setBgColor('#59C0F9')
            // .setTextColor('#0C0C0C')
            // .on('click', () => {
            //     navigate("/app/order");
            // });

            // mainButton.show();
            // mainButton.enable();

            mainButton.hide();

            // return <div className={styles.bottom_name}>@ezshop</div>
        }else{

            mainButton.show();

            mainButton
            .setText("Корзина " + "(" + sumBuyCount() + ")")

            // return <div className={styles.bottom_basket} onClick={() => navigate("/app/basket")}>Корзина ({sumBuyCount()})</div>
        }
    }


    return (
        <div className={styles.main_content}>

        <div className={styles.header}>
            <p className={styles.title}>{t('catalog__catalog')}</p>
            <div className={styles.icon_container}>
                <img className={styles.search_icon} src={search_icon} onClick={focusInput}></img>
                <img className={styles.filter_icon} src={filter_icon} onClick={() => navigate("/app/filter")}></img>
            </div>
        </div>

        <div className={styles.search_input}>
            <img className={styles.search_2_icon} src={search_2_icon}></img>
            <input className={styles.input} ref={inputRef} onChange={(event) => setSearchValue(event.target.value)} placeholder={t('catalog__search_product')}></input>
        </div>
        
        <div className={styles.product_list_scroll}>
             {filterAndSortArray().length == 0 ?
                <div className={styles.empty_msg}>
                    <p className={styles.empty_msg_text}>Товары по данным параметрам отсутствуют</p>
                    <img className={styles.empty_msg_img} src={empty_catalog_img}></img>

                </div>
            : 
            <div className={styles.product_list}>
             {filterAndSortArray().map(product => (
                <ProductCard product={product}></ProductCard>
             ))}
             </div>
             }
        </div>


        {getBottomButton()}

        </div>
    );

}


export default Catalog;