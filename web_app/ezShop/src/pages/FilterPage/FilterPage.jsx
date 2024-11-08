import styles from './FilterPage.module.scss';
import { useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from "react-router-dom";
import {ReactComponent as CrossIcon} from "../../shared/icon/cross-icon.svg";
import { useEffect, useState } from 'react';
import { setFilter } from '../../shared/redux/action/FilterAction';
import { initBackButton } from '@telegram-apps/sdk';
import { initMainButton } from '@telegram-apps/sdk';


function FilterPage({mainButton}){

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const filter = useSelector(state => state.filter);
    const navigate = useNavigate();
    const sortFilter = [t('filters__sort_2'), t('filters__sort_3')]
    const [shopCategories, setShopCategories] = useState([])
    const botId = useSelector(state => state.botId.botId);
    const categories = useSelector(state => state.categories.categories);

    useEffect(() => {

        const [backButton] = initBackButton();
        backButton.show();
        backButton.on('click', backButtonListener, true);

        console.log("filter.categories")
        console.log(filter.categories)

        mainButton
            .setText("Применить")
            .setBgColor("#9edcff")
            .setTextColor('#0C0C0C')
            .enable()
            .show()
            .on('click', mainButtonListener, true);

        // const url = `https://ezbots.ru:${process.env.REACT_APP_API_PORT}/api/categories/get_all_categories/${botId}`;
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

        //     setShopCategories(data)
            
        // })
        // .catch(error => {
        //     console.error('Error:', error);
        // });

        return () => {
            mainButton.off('click', mainButtonListener)
            backButton.off('click', backButtonListener)
        }
    }, []);

    function mainButtonListener() {
        navigate("/app/catalog");
    }

    function backButtonListener() {
       navigate("/app/catalog")
    }

    
    function isEqual(obj1, obj2) {
        // Если оба значения одинаковые
        if (obj1 === obj2) return true;
    
        // Если один из объектов - это null или они разных типов
        if (obj1 == null || obj2 == null || typeof obj1 !== 'object' || typeof obj2 !== 'object') {
            return false;
        }
    
        // Получаем массив ключей объектов
        const keys1 = Object.keys(obj1);
        const keys2 = Object.keys(obj2);
    
        // Если количество ключей не совпадает
        if (keys1.length !== keys2.length) return false;
    
        // Сравниваем значения каждого свойства
        for (let key of keys1) {
            if (!keys2.includes(key) || !isEqual(obj1[key], obj2[key])) {
                return false;
            }
        }
    
        return true;
    }

    const handleFromInputChange = (event) => {
        console.log(event.target.value)
        if(event.target.value == ""){
            filter.priceFrom = null
        }else{
            filter.priceFrom = event.target.value
        }
        dispatch(setFilter(filter))
    };

    const handleBeforeInputChange = (event) => {
        if(event.target.value == ""){
            filter.priceBefore = null
        }else{
            filter.priceBefore = event.target.value
        }
        dispatch(setFilter(filter))
    };

    function getBottomButton(){
        if (filter.priceBefore == null && filter.priceFrom == null && filter.sortType == 'none' && filter.categories.length == 0){
            // return <div className={styles.bottom_name}>@ezshop</div>
        }else{
            // return <div className={styles.bottom_btn} onClick={() => navigate("/app/catalog")}>Применить</div>
        }
    }

    return (
        <div className={styles.main_content}>

        <div className={styles.header}>
            <p className={styles.title}>{t('filters__filters')}</p>
            <CrossIcon className={styles.cross_icon} onClick={() => navigate("/app/catalog")}></CrossIcon>
        </div>

        <p className={styles.input_title}>{t('filters__price')}</p>

        <div className={styles.price_container}>
            <input className={styles.input} placeholder={t('filters__from')} defaultValue={filter.priceFrom} onChange={handleFromInputChange}></input>
            <input className={styles.input} placeholder={t('filters__before')} defaultValue={filter.priceBefore} onChange={handleBeforeInputChange}></input>
        </div>

        <p className={styles.input_title}>{t('filters__sort_title')}</p>

        <div className={styles.sort_container}>
            { sortFilter.map(sortItem => (
                <p className={sortItem == filter.sortType ? styles.sort_item_active : styles.sort_item} onClick={ () => {
                    if (sortItem == filter.sortType){
                        filter.sortType = 'none'
                    }else{
                        filter.sortType=sortItem;
                    }
                    dispatch(setFilter(filter));
                } }>{sortItem}</p>
            ))}
        </div>

        <div className={styles.separator}></div>

        <p className={styles.input_title}>{t('filters__categories')}</p>

        <div className={styles.categories_container}>

            { categories.map(category => (
                <p className={filter.categories.map(i => i.id).includes(category.id) ? styles.category_active : styles.category} onClick={ () => {

                    if (filter.categories.map(i => i.id).includes(category.id)){
                        filter.categories = filter.categories.filter(item => item.id !== category.id);
                    }else{
                        filter.categories = filter.categories.concat(category);
                    }
                    dispatch(setFilter(filter));

                } }>{category.name}</p>
            ))}

        </div>

        {getBottomButton()}

        </div>
    )

}

export default FilterPage;