import styles from './BlockOption.module.scss';
import DropDownCard from '../DropDownCard/DropDownCard';

function BlockOption({data}) {

    return (
        <DropDownCard title={data.name} isDropDownStart={true}>
            <div className={styles.variant_container_scroll}>
                <div className={styles.variant_container}>
                {data.variants.map(item => {
                    return(
                    <p className={styles.item}>{item}</p>
                    )
                })}
                </div>
            </div>
        </DropDownCard>
    );

}

export default BlockOption;