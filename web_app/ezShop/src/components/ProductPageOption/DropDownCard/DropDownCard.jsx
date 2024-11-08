import styles from './DropDownCard.module.scss';
import { useTranslation } from 'react-i18next';
import filter_icon from '../../../shared/icon/filter-icon.svg';
import search_icon from '../../../shared/icon/search-icon.svg';
// import drop_down_icon from '../../../shared/icon/drop-down-icon.svg';
import {ReactComponent as DropDownIcon} from '../../../shared/icon/drop-down-icon.svg';
import { useDispatch, useSelector } from 'react-redux';
import { setProductList } from '../../../shared/redux/action/ProductListAction';
import { useState } from 'react';


function DropDownCard({children, isDropDownStart, title}) {

    const {t, i18n} = useTranslation();

    const [isDropDown, setIsDropDown] = useState(isDropDownStart)

    return (
        <div className={styles.drop_down_card}>
            <div className={styles.top_container} onClick={() => {setIsDropDown(!isDropDown)}}>
                <pre className={styles.title}>{title}</pre>
                {/* <img className={isDropDown ? styles.icon : styles.icon_active} src={drop_down_icon}></img> */}
                <DropDownIcon className={isDropDown ? styles.icon : styles.icon_active}></DropDownIcon>
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