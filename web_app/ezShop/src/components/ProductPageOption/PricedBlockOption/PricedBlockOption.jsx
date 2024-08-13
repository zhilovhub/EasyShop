import styles from './PricedBlockOption.module.scss';
import DropDownCard from '../DropDownCard/DropDownCard';


function PricedBlockOption({data}) {

    console.log(data)
    
    return (
        <DropDownCard title={data.name} isDropDownStart={true}>
            <div className={styles.variant_container_scroll}>
                <div className={styles.variant_container}>
                {data.variants.map((item, index) => {
                    return(
                    <div className={styles.variant_block}>
                        <p className={styles.top_item}>{item}</p>
                        <p className={styles.bottom_item}>{data.variants_prices[index]}</p>
                    </div>
                    )
                })}
                </div>
            </div>
        </DropDownCard>
    );

}

export default PricedBlockOption;