import styles from './Сatalog.module.scss';
import { useTranslation } from 'react-i18next';
import {ReactComponent as SearchIcon} from '../../shared/icon/search-icon.svg';
import {ReactComponent as FilterIcon} from '../../shared/icon/filter-icon.svg';
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
import { on } from '@telegram-apps/sdk';
import { initThemeParams } from '@telegram-apps/sdk';


function Catalog({mainButton}) {

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const botId = useSelector(state => state.botId.botId);
    const navigate = useNavigate();
    const [searchValue, setSearchValue] = useState('');
    const [products, setProducts] = useState([]);
    const inputRef = useRef(null);
    const filter = useSelector(state => state.filter);
    const [themeParams] = initThemeParams();

    useEffect(() => {
        const currentUrl = window.location.href;
        const myUrl = new URL(currentUrl);
        let newBotId = myUrl.searchParams.get('bot_id');

        if(newBotId){
            dispatch(setBotId(newBotId))
        }

    }, [])

    // const [mainButton] = initMainButton();

    // console.log("FIRST", mainButton.isVisible);

    // mainButton.hide()  // сначала всегда прячем кнопку
    // backButton.hide()  // сначала всегда прячем кнопку (опционально)

    useEffect(() => {

        if (!botId) {
            return
        }

        const url = `https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/settings/get_web_app_options/${botId}`;
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

              const bg_color = data.theme_params.bg_color;
              const text_color = data.theme_params.text_color;
              const secondary_bg_color = data.theme_params.secondary_bg_color;
              const button_text_color = data.theme_params.button_text_color;
            //   const button_color = data.theme_params.button_color;

              document.documentElement.style.setProperty('--bg_color', bg_color == "telegram" ? (themeParams.get('bgColor') == themeParams.get('secondaryBgColor') ? lightenHexColor(themeParams.get('bgColor'), 0.15) : themeParams.get('bgColor')) : bg_color);
              document.documentElement.style.setProperty('--text_color', text_color == "telegram" ? themeParams.get('textColor') : text_color);
              document.documentElement.style.setProperty('--secondary_bg_color', secondary_bg_color == "telegram" ? themeParams.get('secondaryBgColor') : secondary_bg_color);
              document.documentElement.style.setProperty('--button_text_color', button_text_color == "telegram" ? themeParams.get('buttonTextColor') : button_text_color);
            //   document.documentElement.style.setProperty('--button_color', button_color == "telegram" ? themeParams.get('buttonColor') : button_color);

              console.log('bgColor');
              console.log(bg_color == "telegram" ? themeParams.get('bgColor') : bg_color);
              console.log('textColor');
              console.log(text_color == "telegram" ? themeParams.get('textColor') : text_color);
              console.log('secondaryBgColor');
              console.log(secondary_bg_color == "telegram" ? themeParams.get('headerBgColor') : secondary_bg_color);

            })
            .catch(error => {
                console.error('Error:', error);
            });

  }, [botId])


  function lightenHexColor(hex, percent) {
    hex = hex.replace(/^#/, '');

    // Парсим цвет в RGB
    let r = parseInt(hex.substring(0, 2), 16);
    let g = parseInt(hex.substring(2, 4), 16);
    let b = parseInt(hex.substring(4, 6), 16);

    // Увеличиваем цветовые компоненты
    r = Math.min(255, Math.round(r + (255 - r) * percent));
    g = Math.min(255, Math.round(g + (255 - g) * percent));
    b = Math.min(255, Math.round(b + (255 - b) * percent));

    // Преобразуем обратно в hex
    const newHex = '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase();
    return newHex;
    }

    useEffect(() => {
        console.log("useEffect getBottomButton");
        getBottomButton();
    }, [productList]);

    useEffect(() => {
        if (!botId) {
            return
        }

        console.log("useEffect Main");

        const [backButton] = initBackButton();
        backButton.hide();

         mainButton
            .setBgColor("#9edcff")
            .setTextColor('#0C0C0C')
            .enable()
            .on('click', mainButtonListener, true);

        // alert(botId)


        if (productList.length == 0){

        const url = `https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/products/get_all_products?bot_id=${botId}`;
        console.log("URL: " + url)
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
    return () => {
        mainButton.off('click', mainButtonListener);
    }
    }, [botId]);


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

    function mainButtonListener() {
        navigate("/app/basket");
    }

    function getBottomButton(){
        const currentCount = sumBuyCount();
        if (currentCount == 0 || currentCount == null){
            // mainButton
            // .setText("Начать оформление")
            // .setBgColor('#59C0F9')
            // .setTextColor('#0C0C0C')
            // .on('click', () => {
            //     navigate("/app/order");
            // });

            // mainButton.show();
            // mainButton.enable();

            // mainButton.on('isVisible', () => {

            // })

            // mainButton.disable();
            mainButton.hide();

            // return <div className={styles.bottom_name}>@ezshop</div>
        }else{
            mainButton
            .setText("Корзина " + "(" + currentCount + ")")
            .show()  // show делаем после всех конфигураций кнопки

            // return <div className={styles.bottom_basket} onClick={() => navigate("/app/basket")}>Корзина ({sumBuyCount()})</div>
        }
    }


    return (
        <div className={styles.main_content}>

        <div className={styles.header}>
            <p className={styles.title}>{t('catalog__catalog')}</p>
            <div className={styles.icon_container}>
                <SearchIcon className={styles.search_icon} onClick={focusInput}></SearchIcon>
                <FilterIcon className={styles.filter_icon} onClick={() => navigate("/app/filter")}></FilterIcon>
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


         {/* {getBottomButton()} */}

        </div>
    );

}


export default Catalog;