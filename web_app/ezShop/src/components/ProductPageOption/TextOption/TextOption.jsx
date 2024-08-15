import styles from './TextOption.module.scss';
import DropDownCard from '../DropDownCard/DropDownCard';

function TextOption({data}) {

    return (
        <DropDownCard title={data.name} isDropDownStart={true}>
                <p className={styles.text}>{data.variants}</p>
        </DropDownCard>
    );

}

export default TextOption;