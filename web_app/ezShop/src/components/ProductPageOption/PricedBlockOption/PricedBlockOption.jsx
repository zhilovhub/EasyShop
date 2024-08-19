import styles from './PricedBlockOption.module.scss';
import DropDownCard from '../DropDownCard/DropDownCard';
import { useDispatch, useSelector } from 'react-redux';
import { setProductList } from '../../../shared/redux/action/ProductListAction';


function PricedBlockOption({data}) {

    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);


    function onPriceClick(newVariant, status){

        const newProducts = productList.map((product, index) => {
            if (product.id == data.productId){
                product.extra_options = product.extra_options.map(extraOption => {
                    if (extraOption.name == data.name){
                        extraOption.variantsIsSelected = extraOption.variants_prices.map(item => {return false})
                        extraOption.variants.map((variant, index) => {
                            if(variant == newVariant){
                                extraOption.variantsIsSelected[index] = status;
                            }else{
                                extraOption.variantsIsSelected[index] = false;
                            }
                        })
                    }
                    return extraOption;
                })
            }

            return product;
        })
        dispatch(setProductList(newProducts))
    }
    
    return (
        <DropDownCard title={data.name} isDropDownStart={true}>
            <div className={styles.variant_container_scroll}>
                <div className={styles.variant_container}>
                {data.variants.map((item, index) => {
                    return(
                    <div className={data.variantsIsSelected[index] ? styles.variant_block_active : styles.variant_block} onClick={() => onPriceClick(data.variants[index], !data.variantsIsSelected[index])}>
                        <p className={styles.top_item}>{item}</p>
                        <p className={styles.bottom_item}>{data.variants_prices[index]} ₽</p>
                    </div>
                    )
                })}
                </div>
            </div>
        </DropDownCard>
    );

}

export default PricedBlockOption;