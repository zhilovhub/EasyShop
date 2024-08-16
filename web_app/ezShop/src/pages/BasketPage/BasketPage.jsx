import styles from './BasketPage.module.scss';
import { useTranslation } from 'react-i18next';
import layer_plus_icon from '../../shared/icon/layer-plus-icon.svg';
import { useDispatch, useSelector } from 'react-redux';
import ProductCard from '../../components/ProductCard/ProductCard';
import BasketCard from '../../components/BasketCard/BasketCard';
import empty_basket_img from '../../shared/images/empty-basket-img.png';
import { useNavigate } from "react-router-dom";
import { initBackButton } from '@telegram-apps/sdk';
import { useEffect } from 'react';
import { initMainButton } from '@telegram-apps/sdk';


function BasketPage({mainButton}){

    const {t, i18n} = useTranslation();
    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);
    const botId = useSelector(state => state.botId.botId);
    const navigate = useNavigate();


    useEffect(() => {

        const [backButton] = initBackButton();
        backButton.show();
        backButton.on('click', () => {
            navigate(`/app/catalog?bot_id=${botId}`);
        });

        mainButton
        .show()
        .setText("Начать оформление")
        .setBgColor("#9edcff")
        .setTextColor('#0C0C0C')
        .enable()
        .on('click', () => {
                navigate("/app/order");
        }, true);

    }, [])

    // useEffect(() => {
    // }, [productList])

    function filterByBuyCount() {
        return productList.filter(product => product.buyCount !== 0);
    }

    function sumBuyCount() {
        return productList.reduce((total, item) => total + (item.buyCount || 0), 0);
    }

    function getBottomButton(){
        if (sumBuyCount() == 0){

            mainButton
            .setText("К каталогу")
            .setBgColor("#9edcff")
            .setTextColor('#0C0C0C')
            .enable()
            .on('click', () => {
                    navigate("/app/catalog");
            }, true)
            .show();

            // return <div className={styles.bottom_btn} onClick={() => navigate("/app/catalog")}>К каталогу</div>
        }else{



            // return <div className={styles.bottom_btn} onClick={() => navigate("/app/order")}>Начать оформление</div>
        }
    }

    return (
        <div className={styles.main_content}>

        <div className={styles.header}>
            <p className={styles.title}>{t('basket__basket')}</p>
            <img className={styles.layer_plus_icon} src={layer_plus_icon} onClick={() => navigate("/app/catalog")}></img>
        </div>

        { filterByBuyCount().length != 0 ?
        <div className={styles.product_list_scroll}>
             <div className={styles.product_list}>

             {filterByBuyCount().map(product => (
                <BasketCard product={product}></BasketCard>
             ))}

             </div>
        </div>
        :
        <div className={styles.empty_basket}>

            <img className={styles.empty_basket_img} src={empty_basket_img}></img>
            <p className={styles.msg_emty}>{t('basket__msg_emty')}</p>
            <p className={styles.hint_emty}>{t('basket__hint_emty')}</p>

        </div>
        }

        {getBottomButton()}

        </div>
    )
    

   

}

export default BasketPage;