import styles from './DropDownCard.module.scss';
import { useTranslation } from 'react-i18next';
import filter_icon from '../../../shared/icon/filter-icon.svg';
import search_icon from '../../../shared/icon/search-icon.svg';
import drop_down_icon from '../../../shared/icon/drop-down-icon.svg'
import { useDispatch, useSelector } from 'react-redux';
import { setProductList } from '../../../shared/redux/action/ProductListAction';
import { useState } from 'react';


function DropDownCard({children, isDropDownStart, title}) {

    const {t, i18n} = useTranslation();

    const [isDropDown, setIsDropDown] = useState(isDropDownStart)

    return (
        <div className={styles.drop_down_card}>
            <div className={styles.top_container} onClick={() => {setIsDropDown(!isDropDown)}}>
                <p className={styles.title}>{title}</p>
                <img className={isDropDown ? styles.icon : styles.icon_active} src={drop_down_icon}></img>
            </div>

            { isDropDown ?
            <div className={styles.content}>
                {children}
            </div>
                :
            <></>
            }       

        </div>
    );

}

export default DropDownCard;