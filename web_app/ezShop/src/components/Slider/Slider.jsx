import React, { useState } from 'react';
import styles from './Slider.module.scss';
import slider_arrow from '../../shared/icon/slider-arrow.svg'

const Slider = ({urls}) => {
    const images = urls;

    console.log(images)

    const [currentIndex, setCurrentIndex] = useState(0);

    const nextSlide = () => {
        setCurrentIndex((prevIndex) => (prevIndex + 1) % images.length);
    };

    const prevSlide = () => {
        setCurrentIndex((prevIndex) => 
            (prevIndex - 1 + images.length) % images.length
        );
    };

    return (
        <div className={styles.slider}>
            <img className={styles.img} src={images[currentIndex]} alt="slider" />
            {images.length != 1 ?
            <div className={styles.arrow_container}>
                <img className={styles.arrow_left} onClick={() => {if(currentIndex!=0){prevSlide()}}} src={slider_arrow}></img>
                <img className={styles.arrow_right} onClick={() => {if(currentIndex!=(images.length-1)){nextSlide()}}} src={slider_arrow}></img>
            </div>
            :
            <></>
            }
        </div>
    );

};

export default Slider;
