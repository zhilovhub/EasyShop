import styles from './BlockOption.module.scss';
import DropDownCard from '../DropDownCard/DropDownCard';
import { useDispatch, useSelector } from 'react-redux';
import { setProductList } from '../../../shared/redux/action/ProductListAction';

function BlockOption({data}) {

    const dispatch = useDispatch();
    const productList = useSelector(state => state.productList.productList);


    function onOptionClick(newValue, status){

        console.log("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
        console.log(productList)

        const newProducts = productList.map((product, index) => {
            if (product.id == data.productId){
                product.extra_options = product.extra_options.map(extraOption => {
                    if (extraOption.name == data.name){
                        extraOption.variantsIsSelected = extraOption.variants.map(item => {return false})
                        extraOption.variants.map((variant, index) => {
                            if(variant == newValue){
                                extraOption.variantsIsSelected[index] = status;
                            }else{
                                extraOption.variantsIsSelected[index] = false;
                            }
                        })
                    }
                    return extraOption;
                })
            console.log("NEW product")
            console.log(product)
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
                    <p className={data.variantsIsSelected[index] ? styles.item_active : styles.item} onClick={() => {onOptionClick(item, !data.variantsIsSelected[index])}}>{item}</p>
                    )
                })}
                </div>
            </div>
        </DropDownCard>
    );

}

export default BlockOption;