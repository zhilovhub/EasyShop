import styles from './TextOption.module.scss';
import DropDownCard from '../DropDownCard/DropDownCard';

function TextOption({data}) {

    return (
        <DropDownCard title={data.name} isDropDownStart={true}>
                <pre className={styles.text}>{data.variants}</pre>
        </DropDownCard>
    );

}

export default TextOption;